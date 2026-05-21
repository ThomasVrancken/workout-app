"""Firebase Authentication for the Workout Agent backend.

Verifies Firebase ID tokens (issued by Google Sign-In or email/password)
and exposes the authenticated user's UID + email to downstream handlers.
"""

import logging
import os
from dataclasses import dataclass

import firebase_admin
from fastapi import HTTPException, Request, status
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

logger = logging.getLogger(__name__)


_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")


def _init_firebase() -> None:
    """Initialize the Firebase Admin SDK once.

    On Cloud Run this uses the service account attached to the service
    (Application Default Credentials). Locally, the developer should run
    `gcloud auth application-default login` for ADC to work.
    """
    if firebase_admin._apps:
        return

    try:
        firebase_admin.initialize_app(credentials.ApplicationDefault(), {
            "projectId": _PROJECT_ID,
        } if _PROJECT_ID else None)
    except Exception:
        logger.exception("Failed to initialise Firebase Admin SDK")
        raise


_init_firebase()


@dataclass(frozen=True)
class AuthedUser:
    """Authenticated user info extracted from a verified Firebase ID token."""

    uid: str
    email: str | None
    display_name: str | None


async def require_user(request: Request) -> AuthedUser:
    """FastAPI dependency: verify the Firebase ID token in the Authorization header.

    Returns an `AuthedUser` for the request. Raises 401 if the token is
    missing, malformed, or invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token",
        )

    try:
        decoded = firebase_auth.verify_id_token(token, check_revoked=False)
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(status_code=401, detail="Token revoked")
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (firebase_auth.InvalidIdTokenError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        logger.exception("Unexpected error verifying ID token")
        raise HTTPException(status_code=401, detail="Token verification failed")

    user = AuthedUser(
        uid=decoded["uid"],
        email=decoded.get("email"),
        display_name=decoded.get("name"),
    )
    request.state.user = user
    return user
