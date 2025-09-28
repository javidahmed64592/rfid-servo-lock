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
        mock.getmode.return_value = None  # Default to BCM mode
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
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function initialization in BCM mode."""
        # Setup mocks
        mock_gpio.getmode.return_value = None  # BCM mode
        mock_rfid_reader.return_value.read_card.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.INFO):
            run()

        # Verify initialization
        mock_load_dotenv.assert_called_once()
        mock_servo_lock.assert_called_once_with(
            pin=18,
            locked_angle=0,
            unlocked_angle=90,
        )

        # Verify logging messages
        assert "Initializing RFID Servo Lock System..." in caplog.text
        assert "Using BCM mode - Servo on BCM pin 18." in caplog.text
        assert "System initialized successfully!" in caplog.text
        assert "Waiting for RFID cards..." in caplog.text

        # Verify cleanup
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_initialization_board_mode(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function initialization in BOARD mode."""
        # Setup mocks
        mock_gpio.getmode.return_value = mock_gpio.BOARD
        mock_gpio.BOARD = 10  # Mock BOARD constant
        mock_rfid_reader.return_value.read_card.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.INFO):
            run()

        # Verify servo was initialized with BOARD pin
        mock_servo_lock.assert_called_once_with(
            pin=12,
            locked_angle=0,
            unlocked_angle=90,
        )

        # Verify logging messages
        assert "Using BOARD mode - Servo on physical pin 12." in caplog.text

        # Verify cleanup
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_successful_card_authorization(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_verify_card_authorization: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function with successful card authorization."""
        # Setup mocks
        mock_rfid_reader.return_value.read_card.side_effect = [
            (123456789, "test_password"),
            KeyboardInterrupt(),
        ]
        mock_verify_card_authorization.return_value = True

        with caplog.at_level(logging.INFO):
            run()

        # Verify card verification was called
        mock_verify_card_authorization.assert_called_once_with(123456789, "test_password")

        # Verify servo was toggled
        mock_servo_lock.return_value.toggle.assert_called_once()

        # Verify logging messages
        assert "Ready to detect RFID card..." in caplog.text
        assert "Card authorized! Access granted." in caplog.text

        # Verify sleep was called after authorization
        mock_sleep.assert_called_with(1)

        # Verify cleanup
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_failed_card_authorization(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_verify_card_authorization: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function with failed card authorization."""
        # Setup mocks
        mock_rfid_reader.return_value.read_card.side_effect = [
            (987654321, "wrong_password"),
            KeyboardInterrupt(),
        ]
        mock_verify_card_authorization.return_value = False

        with caplog.at_level(logging.WARNING):
            run()

        # Verify card verification was called
        mock_verify_card_authorization.assert_called_once_with(987654321, "wrong_password")

        # Verify servo was NOT toggled
        mock_servo_lock.return_value.toggle.assert_not_called()

        # Verify logging messages
        assert "Card unauthorized! Access denied." in caplog.text

        # Verify sleep was called after authorization attempt
        mock_sleep.assert_called_with(1)

        # Verify cleanup
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_no_card_detected(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_verify_card_authorization: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function when no card is detected."""
        # Setup mocks - return None (no card) then interrupt
        mock_rfid_reader.return_value.read_card.side_effect = [None, KeyboardInterrupt()]

        with caplog.at_level(logging.INFO):
            run()

        # Verify card verification was NOT called
        mock_verify_card_authorization.assert_not_called()

        # Verify servo was NOT toggled
        mock_servo_lock.return_value.toggle.assert_not_called()

        # Verify sleep was NOT called (only called after card data is present)
        mock_sleep.assert_not_called()

        # Verify logging messages
        assert "Ready to detect RFID card..." in caplog.text

        # Verify cleanup
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_keyboard_interrupt_immediate(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function with immediate KeyboardInterrupt."""
        # Setup mocks
        mock_rfid_reader.return_value.read_card.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.INFO):
            run()

        # Verify initialization messages
        assert "Initializing RFID Servo Lock System..." in caplog.text
        assert "System initialized successfully!" in caplog.text
        assert "Shutting down RFID Servo Lock System..." in caplog.text
        assert "System shutdown complete!" in caplog.text

        # Verify cleanup
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_unexpected_exception(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_verify_card_authorization: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function handling unexpected exceptions."""
        # Setup mocks
        mock_rfid_reader.return_value.read_card.side_effect = Exception("Unexpected error!")

        with caplog.at_level(logging.ERROR):
            run()

        # Verify exception was logged
        assert "Unexpected error occurred!" in caplog.text

        # Verify cleanup still occurred
        assert "Cleaning up resources..." in caplog.text
        assert "System shutdown complete!" in caplog.text
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_exception_during_card_verification(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_verify_card_authorization: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function when card verification raises an exception."""
        # Setup mocks
        mock_rfid_reader.return_value.read_card.side_effect = [(123456789, "test_password"), KeyboardInterrupt()]
        mock_verify_card_authorization.side_effect = Exception("Verification error!")

        with caplog.at_level(logging.ERROR):
            run()

        # Verify exception was logged
        assert "Unexpected error occurred!" in caplog.text

        # Verify servo was NOT toggled
        mock_servo_lock.return_value.toggle.assert_not_called()

        # Verify cleanup still occurred
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_exception_during_servo_toggle(
        self,
        mock_gpio: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_servo_lock: MagicMock,
        mock_verify_card_authorization: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function when servo toggle raises an exception."""
        # Setup mocks
        mock_rfid_reader.return_value.read_card.side_effect = [(123456789, "test_password"), KeyboardInterrupt()]
        mock_verify_card_authorization.return_value = True
        mock_servo_lock.return_value.toggle.side_effect = Exception("Servo error!")

        with caplog.at_level(logging.ERROR):
            run()

        # Verify card was verified
        mock_verify_card_authorization.assert_called_once_with(123456789, "test_password")

        # Verify servo toggle was attempted
        mock_servo_lock.return_value.toggle.assert_called_once()

        # Verify exception was logged
        assert "Unexpected error occurred!" in caplog.text

        # Verify cleanup still occurred
        mock_servo_lock.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()
