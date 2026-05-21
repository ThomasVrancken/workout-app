"""User storage in Firestore with at-rest encryption for the Hevy API key.

Data model (collection `users`):
    {uid}:
        email: str | None
        displayName: str | None
        hevyApiKey: str | None        # Fernet-encrypted ciphertext (urlsafe base64)
        consentedAt: datetime | None
        consentVersion: str | None    # e.g. "2026-05-18"
        createdAt: datetime
        lastActiveAt: datetime

Chat history is **never** persisted server-side.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from google.cloud import firestore

logger = logging.getLogger(__name__)


CONSENT_VERSION = "2026-05-18"

_USERS_COLLECTION = "users"

_ENCRYPTION_KEY_ENV = "ENCRYPTION_KEY"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_fernet() -> Fernet:
    """Return a Fernet instance built from the server-side encryption key.

    The key must be a 32-byte urlsafe base64 string. Generate one with:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    key = os.environ.get(_ENCRYPTION_KEY_ENV)
    if not key:
        raise RuntimeError(
            f"{_ENCRYPTION_KEY_ENV} env var is not set. "
            "Generate one with `python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"`."
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        raise RuntimeError(f"Invalid {_ENCRYPTION_KEY_ENV}: {exc}") from exc


def encrypt_api_key(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Failed to decrypt Hevy API key") from exc


def mask_api_key(plaintext: str) -> str:
    """Return a masked representation of an API key for display."""
    if not plaintext:
        return ""
    if len(plaintext) <= 6:
        return "•" * len(plaintext)
    return f"{plaintext[:4]}{'•' * 6}{plaintext[-4:]}"


@dataclass
class UserRecord:
    uid: str
    email: str | None
    display_name: str | None
    hevy_api_key_encrypted: str | None
    consented_at: datetime | None
    consent_version: str | None
    created_at: datetime | None
    last_active_at: datetime | None

    @property
    def has_hevy_key(self) -> bool:
        return bool(self.hevy_api_key_encrypted)

    @property
    def has_current_consent(self) -> bool:
        return self.consent_version == CONSENT_VERSION

    def decrypted_hevy_key(self) -> str | None:
        if not self.hevy_api_key_encrypted:
            return None
        return decrypt_api_key(self.hevy_api_key_encrypted)

    def to_public_dict(self) -> dict[str, Any]:
        """Public profile shape returned by the API.

        Never includes the encrypted ciphertext; only a masked version of the
        decrypted key (if one is set) for UI display.
        """
        masked = None
        if self.hevy_api_key_encrypted:
            try:
                masked = mask_api_key(self.decrypted_hevy_key() or "")
            except Exception:
                masked = "••••"

        return {
            "uid": self.uid,
            "email": self.email,
            "displayName": self.display_name,
            "hasHevyKey": self.has_hevy_key,
            "hevyKeyMasked": masked,
            "consentVersion": self.consent_version,
            "currentConsentVersion": CONSENT_VERSION,
            "hasCurrentConsent": self.has_current_consent,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "lastActiveAt": self.last_active_at.isoformat() if self.last_active_at else None,
        }


class UserStore:
    """Thin Firestore wrapper for the users collection."""

    def __init__(self, client: firestore.Client | None = None):
        self._client = client or firestore.Client()

    def _doc(self, uid: str) -> firestore.DocumentReference:
        return self._client.collection(_USERS_COLLECTION).document(uid)

    def get(self, uid: str) -> UserRecord | None:
        snap = self._doc(uid).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        return UserRecord(
            uid=uid,
            email=data.get("email"),
            display_name=data.get("displayName"),
            hevy_api_key_encrypted=data.get("hevyApiKey"),
            consented_at=data.get("consentedAt"),
            consent_version=data.get("consentVersion"),
            created_at=data.get("createdAt"),
            last_active_at=data.get("lastActiveAt"),
        )

    def upsert_on_login(
        self,
        uid: str,
        email: str | None,
        display_name: str | None,
    ) -> UserRecord:
        """Create the user doc on first login, or update lastActiveAt on returning logins."""
        ref = self._doc(uid)
        snap = ref.get()
        now = _utcnow()
        if not snap.exists:
            ref.set({
                "email": email,
                "displayName": display_name,
                "hevyApiKey": None,
                "consentedAt": None,
                "consentVersion": None,
                "createdAt": now,
                "lastActiveAt": now,
            })
        else:
            updates: dict[str, Any] = {"lastActiveAt": now}
            if email and email != snap.get("email"):
                updates["email"] = email
            if display_name and display_name != snap.get("displayName"):
                updates["displayName"] = display_name
            ref.update(updates)

        record = self.get(uid)
        assert record is not None
        return record

    def set_consent(self, uid: str, version: str = CONSENT_VERSION) -> None:
        self._doc(uid).update({
            "consentedAt": _utcnow(),
            "consentVersion": version,
        })

    def set_hevy_key(self, uid: str, plaintext_key: str) -> None:
        encrypted = encrypt_api_key(plaintext_key.strip())
        self._doc(uid).update({"hevyApiKey": encrypted})

    def delete_hevy_key(self, uid: str) -> None:
        self._doc(uid).update({"hevyApiKey": None})

    def delete_user(self, uid: str) -> None:
        self._doc(uid).delete()
