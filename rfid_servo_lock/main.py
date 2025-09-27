"""Main application for RFID-controlled servo lock system."""

import logging
import time

from RPi import GPIO

from rfid_servo_lock.rfid import RFIDReader
from rfid_servo_lock.servo import ServoLock

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


def run() -> None:
    """Run the RFID-controlled servo lock system."""
    logger.info("Initializing RFID Servo Lock System...")
    rfid_reader = RFIDReader()

    current_gpio_mode = GPIO.getmode()
    logger.info("GPIO mode detected: %s", current_gpio_mode)

    # Convert pin number based on detected mode
    # Pin mapping reference:
    # - BCM Pin 18 = Physical Pin 12 = BOARD Pin 12
    # - This is GPIO18 on the Raspberry Pi
    if current_gpio_mode == GPIO.BOARD:
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
    logger.info("Waiting for RFID cards... (Press Ctrl+C to exit)")

    try:
        while True:
            logger.info("Ready to detect RFID card...")
            card_data = rfid_reader.read_card()

            if card_data:
                if card_data[1]:
                    logger.info("Authorised!")
                    servo_lock.toggle()

                    status = "LOCKED" if servo_lock.is_locked else "UNLOCKED"
                    logger.info("Lock status changed to: %s", status)
                else:
                    logger.warning("Unauthorised card detected! Access denied.")

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
