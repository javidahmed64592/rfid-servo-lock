"""RFID reader/writer module for MFRC522."""

import logging
import time

from mfrc522 import SimpleMFRC522
from RPi import GPIO

from rfid_servo_lock.auth import save_authorized_card

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


class RFIDReader:
    """Class for handling RFID operations using MFRC522."""

    def __init__(self) -> None:
        """Initialize the RFID reader."""
        self.reader = SimpleMFRC522()

    def read_card(self) -> tuple[int, str] | None:
        """Read data from an RFID card.

        :return: Tuple of (card_id, text) if card is detected, None otherwise.
        """
        try:
            card_id, text = self.reader.read()
            logger.info(str(f"Card detected - ID: {card_id}"))
        except Exception:
            logger.exception("Error reading card!")
            return None
        else:
            return (card_id, text)

    def write_card(self, text: str) -> bool:
        """Write data to an RFID card.

        :param str text: The text to write to the card.
        :return: True if write successful, False otherwise.
        """
        try:
            self.reader.write(text)
            logger.info("Data writing is complete")
        except Exception:
            logger.exception("Error writing to card!")
            return False
        else:
            return True


def read() -> None:
    """Read data from RFID cards using the RFIDReader class."""
    rfid = RFIDReader()

    logger.info("RFID Reader - Press Ctrl+C to exit")
    logger.info("-" * 30)

    try:
        while True:
            logger.info("Place the card on the reader...")
            card_data = rfid.read_card()
            if card_data:
                logger.info(str(f"Text: {card_data[1]}"))
            time.sleep(3)
    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        GPIO.cleanup()
        logger.info("Cleanup complete.")


def write() -> None:
    """Write data to RFID cards using the RFIDReader class."""
    rfid_reader = RFIDReader()

    logger.info("RFID Card Writer - Press Ctrl+C to exit")
    logger.info("This will write a password to the card and save the hash to .env")
    logger.info("-" * 50)

    try:
        while True:
            password = input("Enter password for RFID card (or 'quit' to exit): ").strip()

            if password.lower() in ["quit", "q", "exit"]:
                break

            if password:
                logger.info("Place the card on the reader to get its ID...")
                card_data = rfid_reader.read_card()

                if not card_data:
                    logger.error("Failed to read card ID!")
                    continue

                card_id, _ = card_data

                try:
                    save_authorized_card(card_id, password)
                    logger.info("Password hash saved for card %s", card_id)
                except Exception:
                    logger.exception("Failed to save password hash")
                    continue

                # Write the password to the RFID card
                logger.info("Now place the card back on the reader to write the password...")
                success = rfid_reader.write_card(password)

                if success:
                    logger.info("Card %s is now authorized for the lock system.", card_id)
                else:
                    logger.error("Failed to write password to card!")
            else:
                logger.error("Password cannot be empty!")

            logger.info("-" * 50)
    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        GPIO.cleanup()
        logger.info("Cleanup complete.")
