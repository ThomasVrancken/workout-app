"""Per-request agent: spawn a fresh `hevy-mcp` subprocess with the user's API key.

The previous version held a single MCP session for the lifetime of the app
(one shared Hevy account). With multi-user support, each chat request now
runs against the requesting user's own Hevy API key, so we spawn a short-lived
MCP subprocess per request.

`hevy-mcp` is pre-installed globally in the Docker image, so spawning is fast
(~200ms, dwarfed by LLM latency).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from mcp import StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.txt"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")


def _load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text().strip()


def _build_contents(history: list[dict], message: str) -> list[types.Content]:
    contents: list[types.Content] = []
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
    history = getattr(response, "automatic_function_calling_history", None)
    if not history:
        return []

    tool_calls: list[dict] = []
    for content in history:
        if not content.parts:
            continue
        for part in content.parts:
            if part.function_call:
                tool_calls.append({
                    "name": part.function_call.name,
                    "args": _safe_serialize(part.function_call.args),
                })
            elif part.function_response:
                for tc in reversed(tool_calls):
                    if tc["name"] == part.function_response.name and "result" not in tc:
                        tc["result"] = _safe_serialize(part.function_response.response)
                        break
    return tool_calls


class WorkoutAgent:
    """Stateless agent. The Gemini client is a singleton (not user-specific);
    each `chat()` call spawns its own short-lived `hevy-mcp` subprocess.
    """

    def __init__(self) -> None:
        self._genai_client: genai.Client | None = None

    def _client(self) -> genai.Client:
        if self._genai_client is None:
            self._genai_client = genai.Client(
                vertexai=True,
                project=os.environ["GOOGLE_CLOUD_PROJECT"],
                location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
            )
        return self._genai_client

    async def chat(
        self,
        message: str,
        history: list[dict] | None,
        hevy_api_key: str,
    ) -> dict:
        """Send a message and return ``{"text": ..., "tool_calls": [...]}``.

        Spawns a fresh `hevy-mcp` subprocess for this single request, configured
        with the user's own Hevy API key.
        """
        if not hevy_api_key:
            raise ValueError("hevy_api_key is required to chat")

        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "hevy-mcp"],
            env={**os.environ, "HEVY_API_KEY": hevy_api_key},
        )

        contents = _build_contents(history or [], message)
        system_prompt = _load_system_prompt()
        client = self._client()

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                response = await client.aio.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        tools=[session],
                        temperature=0.7,
                    ),
                )

        text = response.text or "I wasn't able to generate a response. Please try again."
        tool_calls = _extract_tool_calls(response)
        return {"text": text, "tool_calls": tool_calls}
