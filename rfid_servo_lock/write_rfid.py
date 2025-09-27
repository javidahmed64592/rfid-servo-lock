"""RFID card writing utility using the RFIDReader class."""

from rfid_servo_lock.rfid import RFIDReader


def main() -> None:
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


if __name__ == "__main__":
    main()
