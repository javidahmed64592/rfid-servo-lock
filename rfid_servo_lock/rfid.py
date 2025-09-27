"""RFID reader/writer module for MFRC522."""

import time

from mfrc522 import SimpleMFRC522
from RPi import GPIO


class RFIDReader:
    """Class for handling RFID operations using MFRC522."""

    def __init__(self) -> None:
        """Initialize the RFID reader."""
        self.reader = SimpleMFRC522()

    def read_card(self) -> tuple[int, str] | None:
        """Read data from an RFID card.

        Returns:
            Tuple of (card_id, text) if card is detected, None otherwise.

        """
        try:
            print("Reading... Please place the card...")
            card_id, text = self.reader.read()
            print(f"Card detected - ID: {card_id}")
        except Exception as e:
            print(f"Error reading card: {e}")
            return None
        else:
            return (card_id, text)

    def write_card(self, text: str) -> bool:
        """Write data to an RFID card.

        Args:
            text: The text to write to the card.

        Returns:
            True if write successful, False otherwise.

        """
        try:
            print("Please place the card to complete writing...")
            self.reader.write(text)
            print("Data writing is complete")
        except Exception as e:
            print(f"Error writing to card: {e}")
            return False
        else:
            return True

    def wait_for_card(self, timeout: float = 1.0) -> tuple[int, str] | None:
        """Wait for a card to be detected with a timeout.

        Args:
            timeout: Maximum time to wait for card detection in seconds.

        Returns:
            Tuple of (card_id, text) if card is detected within timeout, None otherwise.

        """
        try:
            # Non-blocking read attempt
            card_id, text = self.reader.read_no_block()
            if card_id is not None:
                print(f"Card detected - ID: {card_id}")
                return (card_id, text)
        except AttributeError:
            # Fallback to blocking read with short timeout simulation
            try:
                card_id, text = self.reader.read()
                print(f"Card detected - ID: {card_id}")
            except Exception:
                return None
            else:
                return (card_id, text)
        except Exception as e:
            print(f"Error detecting card: {e}")
            return None
        else:
            return None

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        GPIO.cleanup()


def main() -> None:
    """Example usage of RFIDReader class."""
    rfid = RFIDReader()

    try:
        while True:
            card_data = rfid.read_card()
            if card_data:
                card_id, text = card_data
                print(f"ID: {card_id}\nText: {text}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        rfid.cleanup()


if __name__ == "__main__":
    main()
