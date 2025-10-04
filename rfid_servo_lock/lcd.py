"""LCD1602 display control module for Raspberry Pi."""

import logging
import time

from RPi import GPIO

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


class LCD1602:
    """Class for controlling a 16x2 character LCD display."""

    # LCD Commands
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80

    # Entry mode flags
    LCD_ENTRYRIGHT = 0x00
    LCD_ENTRYLEFT = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_ENTRYSHIFTDECREMENT = 0x00

    # Display control flags
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00

    # Display/cursor shift flags
    LCD_DISPLAYMOVE = 0x08
    LCD_CURSORMOVE = 0x00
    LCD_MOVERIGHT = 0x04
    LCD_MOVELEFT = 0x00

    # Function set flags
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00

    def __init__(
        self,
        pin_rs: int = 27,
        pin_e: int = 22,
        pins_db: list[int] | None = None,
    ) -> None:
        """Initialize the LCD display.

        :param int pin_rs: GPIO pin for Register Select (RS).
        :param int pin_e: GPIO pin for Enable (E).
        :param list[int] | None pins_db: List of GPIO pins for data bus (D4-D7).
        """
        if pins_db is None:
            pins_db = [25, 24, 23, 18]

        self.pin_rs = pin_rs
        self.pin_e = pin_e
        self.pins_db = pins_db
        self.numlines = 2
        self.currline = 0
        self.row_offsets = [0x00, 0x40, 0x14, 0x54]

        self._setup_gpio()
        self._initialize_display()

    def _setup_gpio(self) -> None:
        """Set up GPIO pins for LCD control."""
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.pin_e, GPIO.OUT)
        GPIO.setup(self.pin_rs, GPIO.OUT)

        for pin in self.pins_db:
            GPIO.setup(pin, GPIO.OUT)

    def _initialize_display(self) -> None:
        """Initialize the LCD display with required command sequence."""
        self._write4bits(0x33)  # Initialization
        self._write4bits(0x32)  # Initialization
        self._write4bits(0x28)  # 2 line 5x7 matrix
        self._write4bits(0x0C)  # Turn cursor off (0x0E to enable cursor)
        self._write4bits(0x06)  # Shift cursor right

        self.displaycontrol = self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF
        self.displayfunction = self.LCD_4BITMODE | self.LCD_2LINE | self.LCD_5x8DOTS
        self.displaymode = self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT

        self._write4bits(self.LCD_ENTRYMODESET | self.displaymode)
        self.clear()

    def _delay_microseconds(self, microseconds: int) -> None:
        """Delay for a specified number of microseconds.

        :param int microseconds: Number of microseconds to delay.
        """
        seconds = microseconds / 1_000_000
        time.sleep(seconds)

    def _pulse_enable(self) -> None:
        """Pulse the enable pin to latch data."""
        GPIO.output(self.pin_e, GPIO.LOW)
        self._delay_microseconds(1)
        GPIO.output(self.pin_e, GPIO.HIGH)
        self._delay_microseconds(1)
        GPIO.output(self.pin_e, GPIO.LOW)
        self._delay_microseconds(1)

    def _write4bits(self, bits: int, *, char_mode: bool = False) -> None:
        """Write data to LCD in 4-bit mode.

        :param int bits: 8-bit data to write (sent as two 4-bit operations).
        :param bool char_mode: True for character data, False for commands.
        """
        self._delay_microseconds(1000)
        bits_str = bin(bits)[2:].zfill(8)

        GPIO.output(self.pin_rs, char_mode)

        # Write high nibble
        for pin in self.pins_db:
            GPIO.output(pin, GPIO.LOW)

        for i in range(4):
            if bits_str[i] == "1":
                GPIO.output(self.pins_db[::-1][i], GPIO.HIGH)

        self._pulse_enable()

        # Write low nibble
        for pin in self.pins_db:
            GPIO.output(pin, GPIO.LOW)

        for i in range(4, 8):
            if bits_str[i] == "1":
                GPIO.output(self.pins_db[::-1][i - 4], GPIO.HIGH)

        self._pulse_enable()

    def clear(self) -> None:
        """Clear the display."""
        self._write4bits(self.LCD_CLEARDISPLAY)
        self._delay_microseconds(3000)

    def home(self) -> None:
        """Return cursor to home position (0, 0)."""
        self._write4bits(self.LCD_RETURNHOME)
        self._delay_microseconds(3000)

    def set_cursor(self, col: int, row: int) -> None:
        """Set cursor position on the display.

        :param int col: Column position (0-15 for 16x2 display).
        :param int row: Row position (0-1 for 16x2 display).
        """
        if row >= self.numlines:
            row = self.numlines - 1

        self._write4bits(self.LCD_SETDDRAMADDR | (col + self.row_offsets[row]))

    def display_on(self) -> None:
        """Turn the display on."""
        self.displaycontrol |= self.LCD_DISPLAYON
        self._write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def display_off(self) -> None:
        """Turn the display off."""
        self.displaycontrol &= ~self.LCD_DISPLAYON
        self._write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def cursor_on(self) -> None:
        """Turn the underline cursor on."""
        self.displaycontrol |= self.LCD_CURSORON
        self._write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def cursor_off(self) -> None:
        """Turn the underline cursor off."""
        self.displaycontrol &= ~self.LCD_CURSORON
        self._write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def blink_on(self) -> None:
        """Turn on the blinking cursor."""
        self.displaycontrol |= self.LCD_BLINKON
        self._write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def blink_off(self) -> None:
        """Turn off the blinking cursor."""
        self.displaycontrol &= ~self.LCD_BLINKON
        self._write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def scroll_display_left(self) -> None:
        """Scroll the display to the left."""
        self._write4bits(self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVELEFT)

    def scroll_display_right(self) -> None:
        """Scroll the display to the right."""
        self._write4bits(self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVERIGHT)

    def left_to_right(self) -> None:
        """Set text direction to left-to-right."""
        self.displaymode |= self.LCD_ENTRYLEFT
        self._write4bits(self.LCD_ENTRYMODESET | self.displaymode)

    def right_to_left(self) -> None:
        """Set text direction to right-to-left."""
        self.displaymode &= ~self.LCD_ENTRYLEFT
        self._write4bits(self.LCD_ENTRYMODESET | self.displaymode)

    def autoscroll_on(self) -> None:
        """Enable autoscrolling (right justify text from cursor)."""
        self.displaymode |= self.LCD_ENTRYSHIFTINCREMENT
        self._write4bits(self.LCD_ENTRYMODESET | self.displaymode)

    def autoscroll_off(self) -> None:
        """Disable autoscrolling (left justify text from cursor)."""
        self.displaymode &= ~self.LCD_ENTRYSHIFTINCREMENT
        self._write4bits(self.LCD_ENTRYMODESET | self.displaymode)

    def message(self, text: str) -> None:
        r"""Display a message on the LCD.

        Newline characters (\n) will move to the next line.

        :param str text: Text to display on the LCD.
        """
        logger.debug("Displaying message: %s", text)

        for char in text:
            if char == "\n":
                self._write4bits(0xC0)  # Move to next line
            else:
                self._write4bits(ord(char), char_mode=True)

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        used_pins = [self.pin_rs, self.pin_e, *self.pins_db]
        GPIO.cleanup(used_pins)


def debug() -> None:
    """Demonstrate LCD functionality."""
    GPIO.setmode(GPIO.BCM)
    logger.info("LCD1602 Display Test")
    logger.info("Pin Configuration:")
    logger.info("  RS: BCM 27")
    logger.info("  E:  BCM 22")
    logger.info("  D4: BCM 25")
    logger.info("  D5: BCM 24")
    logger.info("  D6: BCM 23")
    logger.info("  D7: BCM 18")

    lcd = LCD1602()

    try:
        # Welcome message
        lcd.clear()
        lcd.message("Welcome to --->\nRFID Servo Lock")
        time.sleep(3)

        # Animated text demo
        line0 = " Hello, World!"
        line1 = "LCD1602 Test"

        lcd.clear()
        for i, char in enumerate(line0):
            lcd.set_cursor(i, 0)
            lcd.message(char)
            time.sleep(0.1)

        for i, char in enumerate(line1):
            lcd.set_cursor(i, 1)
            lcd.message(char)
            time.sleep(0.1)

        time.sleep(2)

        # Scrolling demo
        logger.info("Scrolling demo...")
        for _ in range(3):
            lcd.scroll_display_left()
            time.sleep(0.5)

        for _ in range(3):
            lcd.scroll_display_right()
            time.sleep(0.5)

        time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        lcd.clear()
        lcd.cleanup()
        GPIO.cleanup()
        logger.info("Cleanup complete.")
