from app.core.constants import BCRYPT_ROUNDS
from app.core.security import (
    DUMMY_HASH,
    hash_password_async,
    verify_password_async,
)


def test_bcrypt_rounds_not_lowered_for_production():
    assert BCRYPT_ROUNDS >= 12


async def test_hash_and_verify_roundtrip():
    hashed = await hash_password_async("password123")
    assert await verify_password_async("password123", hashed) is True
    assert await verify_password_async("wrong-password", hashed) is False


async def test_dummy_hash_never_matches():
    assert await verify_password_async("password123", DUMMY_HASH) is False
