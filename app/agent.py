import json
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.txt"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash")


def _load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text().strip()


def _build_contents(history: list[dict], message: str) -> list[types.Content]:
    """Convert chat history + new message into Gemini Content objects."""
    contents = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
        )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=message)])
    )
    return contents


def _safe_serialize(obj: Any) -> Any:
    """Best-effort conversion to a JSON-serializable structure."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(v) for v in obj]
    try:
        return dict(obj)
    except (TypeError, ValueError):
        return str(obj)


def _extract_tool_calls(response: types.GenerateContentResponse) -> list[dict]:
    """Pull tool-call info out of the automatic function-calling history."""
    history = getattr(response, "automatic_function_calling_history", None)
    if not history:
        return []

    tool_calls: list[dict] = []
    for content in history:
        if not content.parts:
            continue
        for part in content.parts:
            if part.function_call:
                tool_calls.append(
                    {
                        "name": part.function_call.name,
                        "args": _safe_serialize(part.function_call.args),
                    }
                )
            elif part.function_response:
                for tc in reversed(tool_calls):
                    if tc["name"] == part.function_response.name and "result" not in tc:
                        tc["result"] = _safe_serialize(part.function_response.response)
                        break
    return tool_calls


class WorkoutAgent:
    """Manages the MCP server lifecycle and handles chat via Gemini."""

    def __init__(self):
        self._mcp_session: ClientSession | None = None
        self._genai_client: genai.Client | None = None

    @asynccontextmanager
    async def lifespan(self):
        """Start the MCP server and Gemini client; yield while alive."""
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "hevy-mcp"],
            env={
                **os.environ,
                "HEVY_API_KEY": os.environ["HEVY_API_KEY"],
            },
        )

        self._genai_client = genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
        )

        logger.info("Starting hevy-mcp server…")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._mcp_session = session

                tools = await session.list_tools()
                logger.info(f"MCP server ready — {len(tools.tools)} tools available")

                yield

        self._mcp_session = None
        self._genai_client = None
        logger.info("MCP server stopped")

    async def chat(self, message: str, history: list[dict] | None = None) -> dict:
        """Send a message and return ``{"text": ..., "tool_calls": [...]}``."""
        if self._mcp_session is None or self._genai_client is None:
            raise RuntimeError("Agent not initialized — MCP server not running")

        contents = _build_contents(history or [], message)
        system_prompt = _load_system_prompt()

        response = await self._genai_client.aio.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[self._mcp_session],
                temperature=0.7,
            ),
        )

        text = response.text or "I wasn't able to generate a response. Please try again."
        tool_calls = _extract_tool_calls(response)

        return {"text": text, "tool_calls": tool_calls}
