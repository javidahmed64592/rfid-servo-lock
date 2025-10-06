"""Unit tests for the rfid_servo_lock.main module."""

import logging
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from rfid_servo_lock.main import run


@pytest.fixture(autouse=True)
def mock_load_dotenv() -> Generator[MagicMock, None, None]:
    """Fixture to mock load_dotenv."""
    with patch("rfid_servo_lock.main.load_dotenv") as mock:
        yield mock


@pytest.fixture
def mock_gpio() -> Generator[MagicMock, None, None]:
    """Fixture to mock GPIO module."""
    with patch("rfid_servo_lock.main.GPIO") as mock:
        mock.getmode.return_value = None
        yield mock


@pytest.fixture
def mock_rfid_reader() -> Generator[MagicMock, None, None]:
    """Fixture to mock RFIDReader class."""
    with patch("rfid_servo_lock.main.RFIDReader") as mock:
        yield mock


@pytest.fixture
def mock_servo_lock() -> Generator[MagicMock, None, None]:
    """Fixture to mock ServoLock class."""
    with patch("rfid_servo_lock.main.ServoLock") as mock:
        yield mock


@pytest.fixture
def mock_lcd() -> Generator[MagicMock, None, None]:
    """Fixture to mock LCD1602 class."""
    with patch("rfid_servo_lock.main.LCD1602") as mock:
        yield mock


@pytest.fixture
def mock_verify_card_authorization() -> Generator[MagicMock, None, None]:
    """Fixture to mock verify_card_authorization function."""
    with patch("rfid_servo_lock.main.verify_card_authorization") as mock:
        yield mock


@pytest.fixture
def mock_sleep() -> Generator[MagicMock, None, None]:
    """Fixture to mock time.sleep."""
    with patch("rfid_servo_lock.main.time.sleep") as mock:
        yield mock


class TestRun:
    """Unit tests for the run function."""

    def test_run_initialization_bcm_mode(
        self,
        mock_load_dotenv: MagicMock,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_lcd: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function initialization in BCM mode."""
        mock_gpio.getmode.return_value = None
        mock_rfid_reader.return_value.read_card.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.INFO):
            run()

        mock_load_dotenv.assert_called_once()
        mock_lcd.assert_called_once_with(address=0x27, backlight=True)
        assert mock_lcd.return_value.clear.call_count >= 2  # noqa: PLR2004
        assert mock_lcd.return_value.write.call_count >= 4  # noqa: PLR2004
        mock_servo_lock.assert_called_once_with(
            pin=18,
            locked_angle=0,
            unlocked_angle=90,
        )
        assert "Initializing RFID Servo Lock System..." in caplog.text
        assert "Using BCM mode - Servo on BCM pin 18." in caplog.text
        assert "System initialized successfully!" in caplog.text
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_lcd.return_value.set_backlight.assert_called_with(False)  # noqa: FBT003
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_initialization_board_mode(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_lcd: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function initialization in BOARD mode."""
        mock_gpio.BOARD = 10
        mock_gpio.getmode.return_value = mock_gpio.BOARD
        mock_rfid_reader.return_value.read_card.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.INFO):
            run()

        mock_lcd.assert_called_once_with(address=0x27, backlight=True)
        mock_servo_lock.assert_called_once_with(
            pin=12,
            locked_angle=0,
            unlocked_angle=90,
        )
        assert "Using BOARD mode - Servo on physical pin 12." in caplog.text
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_successful_card_authorization(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_lcd: MagicMock,
        mock_verify_card_authorization: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function with successful card authorization."""
        mock_rfid_reader.return_value.read_card.side_effect = [
            (123456789, "test_password"),
            KeyboardInterrupt(),
        ]
        mock_verify_card_authorization.return_value = True

        with caplog.at_level(logging.INFO):
            run()

        mock_verify_card_authorization.assert_called_once_with(123456789, "test_password")
        mock_servo_lock.return_value.toggle.assert_called_once()
        # Verify LCD displays card detection and access granted messages
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        assert any("Card Detected" in str(call) for call in lcd_write_calls)
        assert any("Access Granted" in str(call) for call in lcd_write_calls)
        assert "Ready to detect RFID card..." in caplog.text
        assert "Card authorized! Access granted." in caplog.text
        assert mock_sleep.call_count >= 3  # 0.5s, 2s, 1s delays  # noqa: PLR2004
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_failed_card_authorization(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_lcd: MagicMock,
        mock_verify_card_authorization: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function with failed card authorization."""
        mock_rfid_reader.return_value.read_card.side_effect = [
            (987654321, "wrong_password"),
            KeyboardInterrupt(),
        ]
        mock_verify_card_authorization.return_value = False

        with caplog.at_level(logging.WARNING):
            run()

        mock_verify_card_authorization.assert_called_once_with(987654321, "wrong_password")
        mock_servo_lock.return_value.toggle.assert_not_called()
        # Verify LCD displays access denied message
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        assert any("Access Denied" in str(call) for call in lcd_write_calls)
        assert any("Unauthorized" in str(call) for call in lcd_write_calls)
        assert "Card unauthorized! Access denied." in caplog.text
        assert mock_sleep.call_count >= 3  # 0.5s, 2s, 1s delays  # noqa: PLR2004
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_no_card_detected(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_lcd: MagicMock,
        mock_verify_card_authorization: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function when no card is detected."""
        mock_rfid_reader.return_value.read_card.side_effect = [None, KeyboardInterrupt()]

        with caplog.at_level(logging.INFO):
            run()

        mock_verify_card_authorization.assert_not_called()
        mock_servo_lock.return_value.toggle.assert_not_called()
        # Verify LCD still shows system ready message
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        assert any("System Ready" in str(call) for call in lcd_write_calls)
        assert "Ready to detect RFID card..." in caplog.text
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_keyboard_interrupt_immediate(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_lcd: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function with immediate KeyboardInterrupt."""
        mock_rfid_reader.return_value.read_card.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.INFO):
            run()

        # Verify LCD displays shutdown message
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        assert any("Shutting Down" in str(call) for call in lcd_write_calls)
        assert any("Goodbye!" in str(call) for call in lcd_write_calls)
        assert "Initializing RFID Servo Lock System..." in caplog.text
        assert "System initialized successfully!" in caplog.text
        assert "Shutting down RFID Servo Lock System..." in caplog.text
        assert "System shutdown complete!" in caplog.text
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_lcd.return_value.set_backlight.assert_called_with(False)  # noqa: FBT003
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_unexpected_exception(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_lcd: MagicMock,
        mock_verify_card_authorization: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function handling unexpected exceptions."""
        mock_rfid_reader.return_value.read_card.side_effect = Exception("Unexpected error!")

        with caplog.at_level(logging.INFO):
            run()

        # Verify LCD displays error message
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        assert any("System Error" in str(call) for call in lcd_write_calls)
        assert any("Check logs!" in str(call) for call in lcd_write_calls)
        assert "Unexpected error occurred!" in caplog.text
        assert "Cleaning up resources..." in caplog.text
        assert "System shutdown complete!" in caplog.text
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_exception_during_card_verification(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_lcd: MagicMock,
        mock_verify_card_authorization: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function when card verification raises an exception."""
        mock_rfid_reader.return_value.read_card.side_effect = [(123456789, "test_password"), KeyboardInterrupt()]
        mock_verify_card_authorization.side_effect = Exception("Verification error!")

        with caplog.at_level(logging.ERROR):
            run()

        # Verify LCD displays error message
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        assert any("System Error" in str(call) for call in lcd_write_calls)
        assert "Unexpected error occurred!" in caplog.text
        mock_servo_lock.return_value.toggle.assert_not_called()
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_exception_during_servo_toggle(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_lcd: MagicMock,
        mock_verify_card_authorization: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function when servo toggle raises an exception."""
        mock_rfid_reader.return_value.read_card.side_effect = [(123456789, "test_password"), KeyboardInterrupt()]
        mock_verify_card_authorization.return_value = True
        mock_servo_lock.return_value.toggle.side_effect = Exception("Servo error!")

        with caplog.at_level(logging.ERROR):
            run()

        mock_verify_card_authorization.assert_called_once_with(123456789, "test_password")
        mock_servo_lock.return_value.toggle.assert_called_once()
        # Verify LCD displays error message after servo failure
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        assert any("System Error" in str(call) for call in lcd_write_calls)
        assert "Unexpected error occurred!" in caplog.text
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()
