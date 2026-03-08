import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

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

    async def chat(self, message: str, history: list[dict] | None = None) -> str:
        """Send a message to the agent and return the text response."""
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

        if response.text:
            return response.text

        return "I wasn't able to generate a response. Please try again."
