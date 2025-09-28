"""Main application for RFID-controlled servo lock system."""

import logging
import time

from dotenv import load_dotenv
from RPi import GPIO

from rfid_servo_lock.auth import verify_card_authorization
from rfid_servo_lock.rfid import RFIDReader
from rfid_servo_lock.servo import ServoLock

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


def run() -> None:
    """Run the RFID-controlled servo lock system."""
    load_dotenv()

    logger.info("Initializing RFID Servo Lock System...")
    rfid_reader = RFIDReader()

    # Convert pin number based on detected mode
    # Pin mapping reference:
    # - BCM Pin 18 = Physical Pin 12 = BOARD Pin 12
    # - This is GPIO18 on the Raspberry Pi
    if GPIO.getmode() == GPIO.BOARD:
        servo_pin = 12
        logger.info("Using BOARD mode - Servo on physical pin 12.")
    else:
        servo_pin = 18
        logger.info("Using BCM mode - Servo on BCM pin 18.")

    servo_lock = ServoLock(
        pin=servo_pin,
        locked_angle=0,
        unlocked_angle=90,
    )

    logger.info("System initialized successfully!")
    logger.info("Waiting for RFID cards...")

    try:
        while True:
            logger.info("Ready to detect RFID card...")
            card_data = rfid_reader.read_card()

            if card_data:
                card_id, card_password = card_data

                # Verify the card password against stored hash
                if verify_card_authorization(card_id, card_password):
                    logger.info("Card authorized! Access granted.")
                    servo_lock.toggle()
                else:
                    logger.warning("Card unauthorized! Access denied.")

                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down RFID Servo Lock System...")
    except Exception:
        logger.exception("Unexpected error occurred!")
    finally:
        logger.info("Cleaning up resources...")
        servo_lock.cleanup()
        GPIO.cleanup()
        logger.info("System shutdown complete!")
