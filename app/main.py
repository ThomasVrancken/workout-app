import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from app.agent import WorkoutAgent
from app.auth import verify_auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

agent = WorkoutAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with agent.lifespan():
        yield


app = FastAPI(lifespan=lifespan, dependencies=[Depends(verify_auth)])

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/sw.js")
async def service_worker():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        result = await agent.chat(req.message, req.history)
        return {"response": result["text"], "tool_calls": result["tool_calls"]}
    except Exception:
        logger.exception("Error in chat")
        return JSONResponse(
            status_code=500,
            content={"response": "Something went wrong. Please try again.", "tool_calls": []},
        )
