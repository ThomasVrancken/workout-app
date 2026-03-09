import os
import hmac

from fastapi import Request, HTTPException


APP_SECRET = os.environ.get("APP_SECRET", "")

OPEN_PATHS = {"/", "/api/health", "/manifest.json", "/sw.js"}


async def verify_auth(request: Request):
    """Dependency that checks the Bearer token against APP_SECRET."""
    if not APP_SECRET:
        return

    if request.url.path in OPEN_PATHS or request.url.path.startswith("/static"):
        return

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")

    token = auth_header.removeprefix("Bearer ")
    if not hmac.compare_digest(token, APP_SECRET):
        raise HTTPException(status_code=401, detail="Invalid authorization")
