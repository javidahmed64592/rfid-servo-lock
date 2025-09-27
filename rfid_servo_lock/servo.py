"""Servo motor control module for lock/unlock operations."""

import logging
import time

from RPi import GPIO

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


class ServoLock:
    """Class for controlling a servo motor as a lock mechanism."""

    def __init__(
        self,
        pin: int = 18,
        locked_angle: int = 0,
        unlocked_angle: int = 90,
        frequency: int = 50,
        min_pulse: int = 500,
        max_pulse: int = 2500,
    ) -> None:
        """Initialize the servo lock.

        :param int pin: GPIO pin number for servo control.
        :param int locked_angle: Angle for locked position (0-180 degrees).
        :param int unlocked_angle: Angle for unlocked position (0-180 degrees).
        :param int frequency: PWM frequency in Hz.
        :param int min_pulse: Minimum pulse width in microseconds.
        :param int max_pulse: Maximum pulse width in microseconds.
        """
        self.pin = pin
        self.locked_angle = locked_angle
        self.unlocked_angle = unlocked_angle
        self.frequency = frequency
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self.pwm = None
        self.is_locked = True

        self._setup_gpio()
        self._initialize_position()

    def _setup_gpio(self) -> None:
        """Set up GPIO configuration for servo control."""
        current_mode = GPIO.getmode()

        if current_mode is None:
            logger.info("No GPIO mode set, defaulting to BCM.")
            GPIO.setmode(GPIO.BCM)
            mode_name = "BCM"
        elif current_mode == GPIO.BCM:
            mode_name = "BCM"
        elif current_mode == GPIO.BOARD:
            mode_name = "BOARD"
        else:
            mode_name = f"Unknown ({current_mode})"

        logger.info(str(f"Servo using GPIO mode {mode_name} & Pin {self.pin}."))

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.pwm.start(0)

    def _initialize_position(self) -> None:
        """Initialize servo to locked position on startup."""
        logger.info("Initializing servo to locked position...")
        self.lock()
        logger.info(str(f"Servo initialized and locked at {self.locked_angle}°"))

    @staticmethod
    def _map_value(
        value: float,
        in_min: float,
        in_max: float,
        out_min: float,
        out_max: float,
    ) -> float:
        """Map a value from one range to another."""
        return (out_max - out_min) * (value - in_min) / (in_max - in_min) + out_min

    def set_angle(self, angle: int) -> None:
        """Set the servo to a specific angle.

        :param int angle: Target angle (0-180 degrees).
        """
        angle = max(0, min(180, angle))
        pulse_width = self._map_value(angle, 0, 180, self.min_pulse, self.max_pulse)
        duty_cycle = self._map_value(pulse_width, 0, 20000, 0, 100)

        if self.pwm:
            self.pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.5)

    def lock(self) -> None:
        """Lock the mechanism by moving to locked position."""
        logger.info("Locking...")
        self.set_angle(self.locked_angle)
        self.is_locked = True

    def unlock(self) -> None:
        """Unlock the mechanism by moving to unlocked position."""
        logger.info("Unlocking...")
        self.set_angle(self.unlocked_angle)
        self.is_locked = False

    def toggle(self) -> None:
        """Toggle between locked and unlocked states."""
        if self.is_locked:
            self.unlock()
        else:
            self.lock()

    def cleanup(self) -> None:
        """Clean up PWM resources (GPIO cleanup handled by main application)."""
        if self.pwm:
            self.pwm.stop()
            self.pwm = None


def debug() -> None:
    """Demonstrate servo lock functionality."""
    GPIO.setmode(GPIO.BCM)
    logger.info("Standalone servo test - using BCM mode.")

    servo_lock = ServoLock()

    try:
        while True:
            command = input("Enter command (lock/unlock/toggle/quit): ").strip().lower()

            if command == "lock":
                servo_lock.lock()
            elif command == "unlock":
                servo_lock.unlock()
            elif command == "toggle":
                servo_lock.toggle()
            elif command in ["quit", "q", "exit"]:
                break
            else:
                logger.warning("Invalid command. Use: lock, unlock, toggle, or quit")

    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        servo_lock.cleanup()
        GPIO.cleanup()
        logger.info("Cleanup complete.")
