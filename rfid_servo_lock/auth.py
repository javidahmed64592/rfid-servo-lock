"""Authentication utilities for RFID password hashing and verification."""

import hashlib
import logging
import os
import secrets

logger = logging.getLogger(__name__)


def hash_password_with_card_id(password: str, card_id: int) -> str:
    """Hash a password using the card ID as salt.

    :param str password: The password to hash.
    :param int card_id: The RFID card ID to use as salt.
    :return: The hashed password.
    """
    salt = str(card_id)
    password_salt = f"{password}{salt}"
    hash_object = hashlib.sha256(password_salt.encode())
    return hash_object.hexdigest()


def verify_password_with_card_id(password: str, card_id: int, stored_hash: str) -> bool:
    """Verify a password against a stored hash using card ID as salt.

    :param str password: The password to verify.
    :param int card_id: The RFID card ID to use as salt.
    :param str stored_hash: The stored password hash.
    :return: True if password matches, False otherwise.
    """
    test_hash = hash_password_with_card_id(password, card_id)
    return secrets.compare_digest(test_hash, stored_hash)


def save_authorized_card(card_id: int, password: str) -> None:
    """Hash a password with card ID and save to environment file.

    This replaces any previously authorized card with the new one.
    Environment variables should be loaded externally (e.g., via .env file with python-dotenv).

    :param int card_id: The RFID card ID.
    :param str password: The password to hash and save.
    """
    hashed_password = hash_password_with_card_id(password, card_id)

    # Write the single authorized card configuration to .env file
    with open(".env", "w") as f:
        f.write("# RFID Servo Lock Environment Configuration\n")
        f.write("# Single authorized card (card ID used as salt)\n")
        f.write(f"AUTHORIZED_CARD_ID={card_id}\n")
        f.write(f"AUTHORIZED_CARD_HASH={hashed_password}\n")


def load_card_hash(card_id: int) -> str | None:
    """Load password hash for the authorized card from environment variables.

    Only returns the hash if the provided card_id matches the authorized card.

    :param int card_id: The RFID card ID to check.
    :return: The stored hash if card is authorized, None otherwise.
    """
    try:
        authorized_card_id_str = os.getenv("AUTHORIZED_CARD_ID")
        authorized_card_hash = os.getenv("AUTHORIZED_CARD_HASH")

        if not authorized_card_id_str or not authorized_card_hash:
            return None

        authorized_card_id = int(authorized_card_id_str)

        if authorized_card_id != card_id:
            return None
    except Exception:
        return None
    else:
        return authorized_card_hash


def verify_card_authorization(card_id: int, card_password: str) -> bool:
    """Verify a card's password authorization.

    :param int card_id: The RFID card ID.
    :param str card_password: The password from the RFID card.
    :return: True if authorized, False otherwise.
    """
    cleaned_password = card_password.strip()
    stored_hash = load_card_hash(card_id)

    if not stored_hash:
        return False

    return verify_password_with_card_id(cleaned_password, card_id, stored_hash)
