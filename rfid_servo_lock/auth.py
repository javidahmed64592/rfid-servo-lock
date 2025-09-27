"""Authentication utilities for RFID password hashing and verification."""

import hashlib
import logging
import os
import secrets

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
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


def save_authorized_card(card_id: int, password: str, env_file: str = ".env") -> None:
    """Hash a password with card ID and save to environment file.

    :param int card_id: The RFID card ID.
    :param str password: The password to hash and save.
    :param str env_file: Path to the environment file.
    """
    hashed_password = hash_password_with_card_id(password, card_id)

    # Read existing env file content
    env_content = {}
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#") and "=" in stripped_line:
                    key, value = stripped_line.split("=", 1)
                    env_content[key.strip()] = value.strip()

    # Update with new password hash for this card ID
    env_content[f"RFID_CARD_{card_id}_HASH"] = hashed_password

    # Write back to file
    with open(env_file, "w") as f:
        f.write("# RFID Servo Lock Environment Configuration\n")
        f.write("# Card authorization hashes (card ID used as salt)\n\n")
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")

    logger.info("Card %s authorization saved to %s", card_id, env_file)


def load_card_hash(card_id: int, env_file: str = ".env") -> str | None:
    """Load password hash for a specific card ID from environment file.

    :param int card_id: The RFID card ID.
    :param str env_file: Path to the environment file.
    :return: The stored hash if found, None otherwise.
    """
    if not os.path.exists(env_file):
        logger.warning("Environment file %s not found!", env_file)
        return None

    env_var = f"RFID_CARD_{card_id}_HASH"

    try:
        with open(env_file) as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line.startswith(f"{env_var}="):
                    return stripped_line.split("=", 1)[1].strip()

        logger.warning("No hash found for card %s!", card_id)
    except Exception:
        logger.exception("Error loading hash for card %s!", card_id)
        return None
    else:
        return None


def verify_card_authorization(card_id: int, card_password: str, env_file: str = ".env") -> bool:
    """Verify a card's password authorization.

    :param int card_id: The RFID card ID.
    :param str card_password: The password from the RFID card.
    :param str env_file: Path to the environment file.
    :return: True if authorized, False otherwise.
    """
    cleaned_password = card_password.strip()
    stored_hash = load_card_hash(card_id, env_file)

    if not stored_hash:
        return False

    return verify_password_with_card_id(cleaned_password, card_id, stored_hash)
