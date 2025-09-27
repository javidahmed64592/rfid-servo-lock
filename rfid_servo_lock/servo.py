"""Servo motor control module for lock/unlock operations."""

import time

from RPi import GPIO


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
        self.is_locked = True  # Assume starts in locked position

        self._setup_gpio()

    def _setup_gpio(self) -> None:
        """Set up GPIO configuration for servo control."""
        # Check if GPIO mode is already set
        try:
            current_mode = GPIO.getmode()
            if current_mode is None:
                GPIO.setmode(GPIO.BCM)
            elif current_mode != GPIO.BCM:
                print(f"Warning: GPIO already set to mode {current_mode}, continuing...")
        except Exception:
            # If getmode fails, try to set BCM mode
            try:
                GPIO.setmode(GPIO.BCM)
            except ValueError:
                print("Warning: GPIO mode already set, continuing...")

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.pwm.start(0)

    def _map_value(
        self,
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
        # Clamp angle to valid range
        angle = max(0, min(180, angle))

        # Convert angle to pulse width
        pulse_width = self._map_value(angle, 0, 180, self.min_pulse, self.max_pulse)

        # Convert pulse width to duty cycle
        duty_cycle = self._map_value(pulse_width, 0, 20000, 0, 100)

        # Apply to servo
        if self.pwm:
            self.pwm.ChangeDutyCycle(duty_cycle)

    def lock(self) -> None:
        """Lock the mechanism by moving to locked position."""
        print("Locking...")
        self.set_angle(self.locked_angle)
        self.is_locked = True
        time.sleep(0.5)  # Allow time for servo to reach position

    def unlock(self) -> None:
        """Unlock the mechanism by moving to unlocked position."""
        print("Unlocking...")
        self.set_angle(self.unlocked_angle)
        self.is_locked = False
        time.sleep(0.5)  # Allow time for servo to reach position

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
    # Create servo lock with default settings
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
                print("Invalid command. Use: lock, unlock, toggle, or quit")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        servo_lock.cleanup()
        GPIO.cleanup()
        print("Cleanup complete.")
