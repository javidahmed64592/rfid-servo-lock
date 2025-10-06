"""Unit tests for the rfid_servo_lock.lcd module."""

import logging
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from rfid_servo_lock.lcd import LCD1602


@pytest.fixture
def mock_smbus() -> Generator[MagicMock, None, None]:
    """Fixture to mock smbus2.SMBus."""
    with patch("rfid_servo_lock.lcd.smbus.SMBus") as mock:
        mock_bus = MagicMock()
        mock.return_value = mock_bus
        yield mock_bus


@pytest.fixture
def mock_sleep() -> Generator[MagicMock, None, None]:
    """Fixture to mock time.sleep."""
    with patch("rfid_servo_lock.lcd.time.sleep") as mock:
        yield mock


class TestLCD1602:
    """Unit tests for the LCD1602 class."""

    def test_init(self, mock_smbus: MagicMock, mock_sleep: MagicMock) -> None:
        """Test LCD1602 initialization."""
        lcd = LCD1602()

        assert lcd.address == 0x27  # noqa: PLR2004
        assert lcd.backlight_enabled is True
        mock_smbus.write_byte.assert_called()

    def test_init_failure(self, mock_smbus: MagicMock) -> None:
        """Test LCD1602 initialization when it fails."""
        mock_smbus.write_byte.side_effect = Exception("I2C error")

        with pytest.raises(Exception, match="I2C error"):
            LCD1602()

    def test_clear(self, mock_smbus: MagicMock, mock_sleep: MagicMock) -> None:
        """Test clear method."""
        lcd = LCD1602()
        mock_smbus.write_byte.reset_mock()

        lcd.clear()

        mock_smbus.write_byte.assert_called()

    def test_clear_exception(
        self, mock_smbus: MagicMock, mock_sleep: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test clear method when an exception occurs."""
        lcd = LCD1602()
        mock_smbus.write_byte.side_effect = Exception("I2C error")

        with caplog.at_level(logging.ERROR):
            lcd.clear()

        assert "Error clearing LCD display!" in caplog.text

    def test_write(self, mock_smbus: MagicMock, mock_sleep: MagicMock) -> None:
        """Test write method."""
        lcd = LCD1602()
        mock_smbus.write_byte.reset_mock()

        lcd.write(0, 0, "Hello")

        mock_smbus.write_byte.assert_called()

    def test_write_exception(
        self, mock_smbus: MagicMock, mock_sleep: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test write method when an exception occurs during character writing."""
        lcd = LCD1602()

        with patch.object(lcd, "_send_data", side_effect=Exception("I2C error")):
            with caplog.at_level(logging.ERROR):
                lcd.write(0, 0, "Test")

        assert "Error writing text to LCD display!" in caplog.text

    def test_set_backlight(self, mock_smbus: MagicMock, mock_sleep: MagicMock) -> None:
        """Test set_backlight method."""
        lcd = LCD1602(backlight=False)
        mock_smbus.write_byte.reset_mock()

        lcd.set_backlight(True)

        assert lcd.backlight_enabled is True
        mock_smbus.write_byte.assert_called_with(lcd.address, 0x08)

    def test_cleanup(self, mock_smbus: MagicMock, mock_sleep: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test cleanup method."""
        lcd = LCD1602()

        with caplog.at_level(logging.INFO):
            lcd.cleanup()

        mock_smbus.close.assert_called_once()
        assert "LCD1602 cleanup complete." in caplog.text

    def test_cleanup_exception(
        self, mock_smbus: MagicMock, mock_sleep: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test cleanup method when an exception occurs."""
        lcd = LCD1602()
        mock_smbus.close.side_effect = Exception("Cleanup error")

        with caplog.at_level(logging.ERROR):
            lcd.cleanup()

        assert "Error during LCD cleanup!" in caplog.text
