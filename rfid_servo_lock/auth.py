"""Authentication utilities for RFID password hashing and verification."""

import hashlib
import logging
import os
import secrets

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_salt() -> str:
    """Generate a cryptographically secure random salt.

    :return: Base64-encoded salt string.
    """
    return secrets.token_hex(32)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash a password with a salt using SHA-256.

    :param str password: The password to hash.
    :param str salt: Optional salt to use. If None, generates a new salt.
    :return: Tuple of (hashed_password, salt).
    """
    if salt is None:
        salt = generate_salt()

    # Combine password and salt, then hash
    password_salt = f"{password}{salt}"
    hash_object = hashlib.sha256(password_salt.encode())
    hashed_password = hash_object.hexdigest()

    logger.info("Password hashed successfully")
    return hashed_password, salt


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    """Verify a password against a stored hash and salt.

    :param str password: The password to verify.
    :param str stored_hash: The stored password hash.
    :param str stored_salt: The stored salt.
    :return: True if password matches, False otherwise.
    """
    # Hash the provided password with the stored salt
    test_hash, _ = hash_password(password, stored_salt)

    # Compare hashes using secure comparison to prevent timing attacks
    is_valid = secrets.compare_digest(test_hash, stored_hash)

    if is_valid:
        logger.info("Password verification successful")
    else:
        logger.warning("Password verification failed")

    return is_valid


def save_password_to_env(password: str, env_file: str = ".env") -> None:
    """Hash a password and save it to an environment file.

    :param str password: The password to hash and save.
    :param str env_file: Path to the environment file.
    """
    hashed_password, salt = hash_password(password)

    # Read existing env file content
    env_content = {}
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#") and "=" in stripped_line:
                    key, value = stripped_line.split("=", 1)
                    env_content[key.strip()] = value.strip()

    # Update with new password hash and salt
    env_content["RFID_PASSWORD_HASH"] = hashed_password
    env_content["RFID_PASSWORD_SALT"] = salt

    # Write back to file
    with open(env_file, "w") as f:
        f.write("# RFID Servo Lock Environment Configuration\n")
        f.write("# Generated automatically - do not edit manually\n\n")
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")

    logger.info("Password hash saved to %s", env_file)


def load_password_from_env(env_file: str = ".env") -> tuple[str, str] | None:
    """Load password hash and salt from environment file.

    :param str env_file: Path to the environment file.
    :return: Tuple of (hash, salt) if found, None otherwise.
    """
    if not os.path.exists(env_file):
        logger.warning("Environment file %s not found", env_file)
        return None

    password_hash = None
    password_salt = None

    try:
        with open(env_file) as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line.startswith("RFID_PASSWORD_HASH="):
                    password_hash = stripped_line.split("=", 1)[1].strip()
                elif stripped_line.startswith("RFID_PASSWORD_SALT="):
                    password_salt = stripped_line.split("=", 1)[1].strip()

        if password_hash and password_salt:
            logger.info("Password credentials loaded from %s", env_file)
            return password_hash, password_salt
    except Exception:
        logger.exception("Error loading password credentials from %s", env_file)
        return None
    else:
        logger.warning("Password credentials not found in %s", env_file)
        return None


def verify_card_password(card_password: str, env_file: str = ".env") -> bool:
    """Verify a card password against stored credentials.

    :param str card_password: The password from the RFID card.
    :param str env_file: Path to the environment file.
    :return: True if authorized, False otherwise.
    """
    credentials = load_password_from_env(env_file)

    if not credentials:
        logger.error("No stored credentials found - card denied")
        return False

    stored_hash, stored_salt = credentials
    return verify_password(card_password, stored_hash, stored_salt)


def main() -> None:
    """Interactive password hash generator for testing."""
    print("RFID Password Hash Generator")
    print("-" * 30)

    password = input("Enter password to hash: ").strip()

    if not password:
        print("Password cannot be empty")
        return

    hashed_password, salt = hash_password(password)

    print(f"\nPassword: {password}")
    print(f"Hash: {hashed_password}")
    print(f"Salt: {salt}")

    # Test verification
    is_valid = verify_password(password, hashed_password, salt)
    print(f"Verification test: {'PASSED' if is_valid else 'FAILED'}")

    # Offer to save to .env
    save_choice = input("\nSave to .env file? (y/n): ").strip().lower()
    if save_choice in ["y", "yes"]:
        save_password_to_env(password)
        print("Password saved to .env file")


if __name__ == "__main__":
    main()
