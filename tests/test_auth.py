import asyncio
import hashlib

import pytest
from fastapi import HTTPException

from patient_platform.api.auth import _hash_api_key, require_role


def _make_user(role: str):
    from patient_platform.api.auth import UserContext
    return UserContext(user_id=1, username="tester", role=role)


def test_hash_api_key_is_deterministic():
    assert _hash_api_key("secret") == hashlib.sha256(b"secret").hexdigest()
    assert _hash_api_key("secret") == _hash_api_key("secret")
    assert _hash_api_key("secret") != _hash_api_key("other")


def test_admin_can_access_admin_endpoint():
    checker = require_role("admin")
    result = asyncio.run(checker(_make_user("admin")))
    assert result.role == "admin"


def test_viewer_cannot_access_admin_endpoint():
    checker = require_role("admin")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(checker(_make_user("viewer")))
    assert exc.value.status_code == 403


def test_analyst_allowed_for_analyst_endpoint():
    checker = require_role("admin", "analyst")
    result = asyncio.run(checker(_make_user("analyst")))
    assert result.role == "analyst"


def test_viewer_denied_for_analyst_endpoint():
    checker = require_role("admin", "analyst")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(checker(_make_user("viewer")))
    assert exc.value.status_code == 403
