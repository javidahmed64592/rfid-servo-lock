"""LCD1602 display control module for I2C interface."""

import logging
import time

import smbus2 as smbus

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


class LCD1602:
    """Class for controlling an LCD1602 display via I2C interface."""

    def __init__(self, address: int = 0x27, backlight: bool = True, bus_number: int = 1) -> None:  # noqa: FBT001, FBT002
        """Initialize the LCD1602 display.

        :param int address: I2C address of the LCD display.
        :param bool backlight: Whether to enable the backlight.
        :param int bus_number: I2C bus number.
        """
        self.address = address
        self.backlight_enabled = backlight
        self.bus = smbus.SMBus(bus_number)

        self._initialize_display()

    def _write_word(self, data: int) -> None:
        """Write a byte to the LCD display.

        :param int data: The byte to write.
        """
        temp = data
        if self.backlight_enabled:
            temp |= 0x08
        else:
            temp &= 0xF7
        self.bus.write_byte(self.address, temp)

    def _send_command(self, command: int) -> None:
        """Send a command to the LCD display.

        :param int command: The command byte to send.
        """
        # Send bit7-4 firstly
        buf = command & 0xF0
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self._write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self._write_word(buf)

        # Send bit3-0 secondly
        buf = (command & 0x0F) << 4
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self._write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self._write_word(buf)

    def _send_data(self, data: int) -> None:
        """Send data to the LCD display.

        :param int data: The data byte to send.
        """
        # Send bit7-4 firstly
        buf = data & 0xF0
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self._write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self._write_word(buf)

        # Send bit3-0 secondly
        buf = (data & 0x0F) << 4
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self._write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self._write_word(buf)

    def _initialize_display(self) -> None:
        """Initialize the LCD display with proper settings."""
        try:
            self._send_command(0x33)  # Must initialize to 8-line mode at first
            time.sleep(0.005)
            self._send_command(0x32)  # Then initialize to 4-line mode
            time.sleep(0.005)
            self._send_command(0x28)  # 2 Lines & 5*7 dots
            time.sleep(0.005)
            self._send_command(0x0C)  # Enable display without cursor
            time.sleep(0.005)
            self._send_command(0x01)  # Clear Screen
            self.bus.write_byte(self.address, 0x08)
            logger.info("LCD1602 display initialized successfully at address 0x%02X", self.address)
        except Exception:
            logger.exception("Failed to initialize LCD1602 display!")
            raise

    def clear(self) -> None:
        """Clear the LCD display."""
        try:
            self._send_command(0x01)
        except Exception:
            logger.exception("Error clearing LCD display!")

    def write(self, x: int, y: int, text: str) -> None:
        """Write text to the LCD display at the specified position.

        :param int x: Column position (0-15).
        :param int y: Row position (0-1).
        :param str text: Text to display.
        """
        # Constrain coordinates to valid ranges
        x = max(0, min(15, x))
        y = max(0, min(1, y))

        # Move cursor to position
        address = 0x80 + 0x40 * y + x
        self._send_command(address)

        # Write each character
        try:
            for char in text:
                self._send_data(ord(char))
        except Exception:
            logger.exception("Error writing text to LCD display!")

    def set_backlight(self, enabled: bool) -> None:  # noqa: FBT001
        """Enable or disable the LCD backlight.

        :param bool enabled: True to enable backlight, False to disable.
        """
        self.backlight_enabled = enabled
        if enabled:
            self.bus.write_byte(self.address, 0x08)
        else:
            self.bus.write_byte(self.address, 0x00)

    def cleanup(self) -> None:
        """Clean up I2C bus resources."""
        try:
            self.bus.close()
            logger.info("LCD1602 cleanup complete.")
        except Exception:
            logger.exception("Error during LCD cleanup!")


def turn_off() -> None:
    """Turn off the LCD display."""
    lcd = LCD1602(address=0x27, backlight=True)
    lcd.clear()
    lcd.set_backlight(False)


def debug() -> None:
    """Demonstrate LCD1602 functionality."""
    lcd = LCD1602(address=0x27, backlight=True)

    try:
        logger.info("Writing text to LCD...")
        lcd.clear()
        lcd.write(4, 0, "Hello")
        lcd.write(7, 1, "world!")

        time.sleep(3)

        logger.info("Testing backlight toggle...")
        lcd.set_backlight(False)
        time.sleep(1)
        lcd.set_backlight(True)

        logger.info("Clearing display...")
        time.sleep(2)
        lcd.clear()

        logger.info("Demo complete!")

    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        lcd.cleanup()
