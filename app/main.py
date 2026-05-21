"""FastAPI app: landing page, auth, chat, and account management."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.agent import WorkoutAgent
from app.auth import AuthedUser, require_user
from app.users import CONSENT_VERSION, UserStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


STATIC_DIR = Path(__file__).parent / "static"
PUBLIC_FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", ""),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
}


agent = WorkoutAgent()
user_store: UserStore | None = None


def _get_user_store() -> UserStore:
    global user_store
    if user_store is None:
        user_store = UserStore()
    return user_store


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Workout Agent")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ── Public routes (no auth) ─────────────────────────────────────────


@app.get("/")
async def landing():
    return FileResponse(STATIC_DIR / "landing.html")


@app.get("/app")
async def chat_app():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/privacy")
async def privacy():
    return FileResponse(STATIC_DIR / "privacy.html")


@app.get("/terms")
async def terms():
    return FileResponse(STATIC_DIR / "terms.html")


@app.get("/sw.js")
async def service_worker():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/manifest.json")
async def manifest():
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/config")
async def public_config():
    """Public Firebase web config used by the frontend SDK.

    These values are safe to expose: Firebase API keys are public by design,
    actual access is gated by Firebase Auth + backend ID token verification.
    """
    return PUBLIC_FIREBASE_CONFIG


# ── Authenticated routes ────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[dict] = Field(default_factory=list)


class ConsentRequest(BaseModel):
    version: str = Field(default=CONSENT_VERSION)


class HevyKeyRequest(BaseModel):
    apiKey: str = Field(..., min_length=8, max_length=512)


@app.get("/api/me")
async def get_me(user: AuthedUser = Depends(require_user)):
    """Return the current user's profile.

    Creates the user document on first call (which is the moment a freshly
    signed-up Firebase user first hits the backend).
    """
    store = _get_user_store()
    record = store.upsert_on_login(user.uid, user.email, user.display_name)
    return record.to_public_dict()


@app.post("/api/me/consent")
async def accept_consent(
    body: ConsentRequest,
    user: AuthedUser = Depends(require_user),
):
    """Record the user's acceptance of the current T&C / Privacy Policy."""
    store = _get_user_store()
    store.upsert_on_login(user.uid, user.email, user.display_name)
    store.set_consent(user.uid, body.version or CONSENT_VERSION)
    record = store.get(user.uid)
    if record is None:
        raise HTTPException(status_code=500, detail="User record not found after consent")
    return record.to_public_dict()


@app.post("/api/me/hevy-key")
async def set_hevy_key(
    body: HevyKeyRequest,
    user: AuthedUser = Depends(require_user),
):
    """Save (or replace) the current user's Hevy API key.

    The key is encrypted at rest with Fernet before being stored in Firestore.
    Requires that the user has already accepted the current T&C version.
    """
    store = _get_user_store()
    record = store.upsert_on_login(user.uid, user.email, user.display_name)
    if not record.has_current_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must accept the Privacy Policy and Terms before connecting Hevy.",
        )
    store.set_hevy_key(user.uid, body.apiKey)
    refreshed = store.get(user.uid)
    return refreshed.to_public_dict() if refreshed else {}


@app.delete("/api/me/hevy-key")
async def delete_hevy_key(user: AuthedUser = Depends(require_user)):
    store = _get_user_store()
    store.delete_hevy_key(user.uid)
    return {"ok": True}


@app.get("/api/me/export")
async def export_me(user: AuthedUser = Depends(require_user)):
    """GDPR data portability: return everything we have stored about the user.

    The Hevy API key is returned encrypted (the user can re-paste their own
    plaintext key any time; we don't expose the decrypted ciphertext, only
    confirm whether one is set).
    """
    store = _get_user_store()
    record = store.get(user.uid)
    if record is None:
        return {"uid": user.uid, "data": None}
    return {
        "uid": record.uid,
        "email": record.email,
        "displayName": record.display_name,
        "hasHevyKey": record.has_hevy_key,
        "consentedAt": record.consented_at.isoformat() if record.consented_at else None,
        "consentVersion": record.consent_version,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "lastActiveAt": record.last_active_at.isoformat() if record.last_active_at else None,
        "note": "Workout messages and chat history are not stored server-side.",
    }


@app.delete("/api/me")
async def delete_me(user: AuthedUser = Depends(require_user)):
    """GDPR right to erasure: delete the user's Firestore record and Firebase Auth account."""
    store = _get_user_store()
    store.delete_user(user.uid)

    try:
        from firebase_admin import auth as firebase_auth

        firebase_auth.delete_user(user.uid)
    except Exception:
        logger.exception("Failed to delete Firebase Auth user; Firestore record was deleted")

    return {"ok": True}


@app.post("/api/chat")
@limiter.limit("30/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    user: AuthedUser = Depends(require_user),
):
    store = _get_user_store()
    record = store.get(user.uid)
    if record is None:
        record = store.upsert_on_login(user.uid, user.email, user.display_name)

    if not record.has_current_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must accept the Privacy Policy and Terms to use the chat.",
        )

    hevy_key = record.decrypted_hevy_key()
    if not hevy_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No Hevy API key configured. Add one in settings before chatting.",
        )

    try:
        result = await agent.chat(body.message, body.history, hevy_key)
        return {"response": result["text"], "tool_calls": result["tool_calls"]}
    except Exception:
        logger.exception("Error in chat for user %s", user.uid)
        return JSONResponse(
            status_code=500,
            content={
                "response": "Something went wrong. Please try again.",
                "tool_calls": [],
            },
        )
