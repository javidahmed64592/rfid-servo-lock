"""Main application for RFID-controlled servo lock system."""

import logging
import time

from dotenv import load_dotenv
from RPi import GPIO

from rfid_servo_lock.auth import verify_card_authorization
from rfid_servo_lock.lcd import LCD1602
from rfid_servo_lock.rfid import RFIDReader
from rfid_servo_lock.servo import ServoLock

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


def run() -> None:
    """Run the RFID-controlled servo lock system."""
    load_dotenv()

    logger.info("Initializing RFID Servo Lock System...")

    # Initialize LCD display
    lcd = LCD1602(address=0x27, backlight=True)
    lcd.clear()
    lcd.write(0, 0, "RFID Lock")
    lcd.write(0, 1, "Initializing...")

    rfid_reader = RFIDReader()

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

    # Display ready message
    lcd.clear()
    lcd.write(0, 0, "System Ready")
    lcd.write(0, 1, "Scan card...")

    try:
        while True:
            logger.info("Ready to detect RFID card...")
            card_data = rfid_reader.read_card()

            if card_data:
                card_id, card_password = card_data

                # Display scanning message
                lcd.clear()
                lcd.write(0, 0, "Card Detected")
                lcd.write(0, 1, f"ID: {card_id}")
                time.sleep(0.5)

                if verify_card_authorization(card_id, card_password):
                    logger.info("Card authorized! Access granted.")
                    lcd.clear()
                    lcd.write(0, 0, "Access Granted")
                    lcd.write(0, 1, "Welcome!")
                    servo_lock.toggle()
                    time.sleep(2)
                else:
                    logger.warning("Card unauthorized! Access denied.")
                    lcd.clear()
                    lcd.write(0, 0, "Access Denied")
                    lcd.write(0, 1, "Unauthorized")
                    time.sleep(2)

                # Return to ready state
                lcd.clear()
                lcd.write(0, 0, "System Ready")
                lcd.write(0, 1, "Scan card...")
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down RFID Servo Lock System...")
        lcd.clear()
        lcd.write(0, 0, "Shutting Down")
        lcd.write(0, 1, "Goodbye!")
        time.sleep(1)
    except Exception:
        logger.exception("Unexpected error occurred!")
        lcd.clear()
        lcd.write(0, 0, "System Error")
        lcd.write(0, 1, "Check logs!")
        time.sleep(2)
    finally:
        logger.info("Cleaning up resources...")
        servo_lock.cleanup()
        lcd.clear()
        lcd.set_backlight(False)
        lcd.cleanup()
        GPIO.cleanup()
        logger.info("System shutdown complete!")
