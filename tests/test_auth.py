"""Unit tests for the rfid_servo_lock.auth module."""

from unittest.mock import MagicMock, call, mock_open, patch

from rfid_servo_lock.auth import (
    hash_password_with_card_id,
    load_card_hash,
    save_authorized_card,
    verify_card_authorization,
    verify_password_with_card_id,
)


def test_hash_password_with_card_id() -> None:
    """Test hashing a password with a card ID."""
    card_id = 123456789
    password = "testpassword"  # noqa: S105
    computed_hash = hash_password_with_card_id(password, card_id)
    assert isinstance(computed_hash, str)
    expected_length = 64  # SHA-256 hash length in hex
    assert len(computed_hash) == expected_length


def test_verify_password_with_card_id() -> None:
    """Test verifying a password against a stored hash."""
    card_id = 987654321
    password = "testpassword"  # noqa: S105
    stored_hash = hash_password_with_card_id(password, card_id)
    assert verify_password_with_card_id(password, card_id, stored_hash)


@patch("builtins.open", new_callable=mock_open)
def test_save_authorized_card(mock_file: MagicMock) -> None:
    """Test saving authorized card to environment file."""
    card_id = 123456789
    password = "testpassword"  # noqa: S105

    save_authorized_card(card_id, password)

    # Verify file was opened for writing
    mock_file.assert_called_once_with(".env", "w")

    # Verify the correct content was written
    expected_calls = [
        call("# RFID Servo Lock Environment Configuration\n"),
        call("# Single authorized card (card ID used as salt)\n"),
        call(f"AUTHORIZED_CARD_ID={card_id}\n"),
        call(f"AUTHORIZED_CARD_HASH={hash_password_with_card_id(password, card_id)}\n"),
    ]
    mock_file().write.assert_has_calls(expected_calls)


@patch("rfid_servo_lock.auth.os.getenv")
def test_load_card_hash(mock_getenv: MagicMock) -> None:
    """Test loading card hash from environment variables."""
    card_id = 123456789
    expected_hash = "test_hash_value"

    # Test successful load
    mock_getenv.side_effect = lambda key: {
        "AUTHORIZED_CARD_ID": str(card_id),
        "AUTHORIZED_CARD_HASH": expected_hash,
    }.get(key)

    result = load_card_hash(card_id)
    assert result == expected_hash

    # Test wrong card ID
    mock_getenv.side_effect = lambda key: {
        "AUTHORIZED_CARD_ID": "999999999",
        "AUTHORIZED_CARD_HASH": expected_hash,
    }.get(key)

    result = load_card_hash(card_id)
    assert result is None


@patch("rfid_servo_lock.auth.load_card_hash")
def test_verify_card_authorization(mock_load_card_hash: MagicMock) -> None:
    """Test card authorization verification."""
    card_id = 123456789
    password = "testpassword"  # noqa: S105
    stored_hash = hash_password_with_card_id(password, card_id)

    # Test successful verification
    mock_load_card_hash.return_value = stored_hash
    assert verify_card_authorization(card_id, password) is True

    # Test with no stored hash
    mock_load_card_hash.return_value = None
    assert verify_card_authorization(card_id, password) is False
