"""Main application for RFID-controlled servo lock system."""

import time

from RPi import GPIO

from rfid_servo_lock.rfid import RFIDReader
from rfid_servo_lock.servo import ServoLock


def run() -> None:
    """Run the RFID-controlled servo lock system."""
    print("Initializing RFID Servo Lock System...")

    # Initialize hardware components
    rfid_reader = RFIDReader()
    servo_lock = ServoLock(
        pin=18,  # GPIO pin for servo
        locked_angle=0,  # Angle for locked position
        unlocked_angle=90,  # Angle for unlocked position
    )

    print("System initialized successfully!")
    print("- Servo is set to locked position")
    print("- Waiting for RFID cards...")
    print("- Press Ctrl+C to exit")
    print("-" * 40)

    try:
        while True:
            # Check for RFID card detection
            card_data = rfid_reader.wait_for_card(timeout=0.5)

            if card_data:
                card_id, text = card_data
                print("RFID Card detected!")
                print(f"Card ID: {card_id}")

                # Toggle lock state when any card is detected
                servo_lock.toggle()

                status = "LOCKED" if servo_lock.is_locked else "UNLOCKED"
                print(f"Lock status: {status}")
                print("-" * 40)

                # Wait a moment to prevent rapid triggering
                time.sleep(2)
            else:
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nShutting down RFID Servo Lock System...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Clean up resources
        print("Cleaning up...")
        servo_lock.cleanup()
        rfid_reader.cleanup()
        GPIO.cleanup()
        print("System shutdown complete.")
