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

        :return: Tuple of (card_id, text) if card is detected, None otherwise.
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

        :param str text: The text to write to the card.
        :return: True if write successful, False otherwise.
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

    def wait_for_card(self, timeout: int = 1) -> tuple[int, str] | None:
        """Wait for a card to be detected with a timeout.

        :param int timeout: Maximum time to wait for card detection in seconds.
        :return: Tuple of (card_id, text) if card is detected within timeout, None otherwise.
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


def write() -> None:
    """Write data to RFID cards using the RFIDReader class."""
    rfid_reader = RFIDReader()

    print("RFID Card Writer")
    print("Press Ctrl+C to exit")
    print("-" * 30)

    try:
        while True:
            text = input("Enter text to write to card (or 'quit' to exit): ").strip()

            if text.lower() in ["quit", "q", "exit"]:
                break

            if text:
                print("Please place the card on the reader...")
                success = rfid_reader.write_card(text)

                if success:
                    print(f"Successfully wrote: '{text}' to card")
                else:
                    print("Failed to write to card")
            else:
                print("Please enter some text to write")

            print("-" * 30)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        rfid_reader.cleanup()
        print("Cleanup complete.")


def read() -> None:
    """Read data from RFID cards using the RFIDReader class."""
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
