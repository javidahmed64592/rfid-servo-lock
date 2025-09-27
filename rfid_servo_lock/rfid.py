"""RFID reader/writer module for MFRC522."""

import logging
import time

from mfrc522 import SimpleMFRC522
from RPi import GPIO

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
            logger.info("Place card on the reader...")
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
    logger.info("-" * 30)

    try:
        while True:
            text = input("Enter text to write to card (or 'quit' to exit): ").strip()

            if text.lower() in ["quit", "q", "exit"]:
                break

            if text:
                logger.info("Place the card on the reader...")
                success = rfid_reader.write_card(text)

                if success:
                    logger.info(str(f"Successfully wrote: '{text}' to card"))
                else:
                    logger.info("Failed to write to card")
            else:
                logger.info("Please enter some text to write")

            logger.info("-" * 30)
    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        GPIO.cleanup()
        logger.info("Cleanup complete.")
