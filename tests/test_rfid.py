"""Unit tests for the rfid_servo_lock.rfid module."""

import logging
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from rfid_servo_lock.rfid import RFIDReader, read, write


@pytest.fixture
def mock_sleep() -> Generator[MagicMock, None, None]:
    """Fixture to mock time.sleep."""
    with patch("rfid_servo_lock.rfid.time.sleep") as mock:
        yield mock


@pytest.fixture
def mock_rfid_reader() -> Generator[MagicMock, None, None]:
    """Fixture to mock RFIDReader class."""
    with patch("rfid_servo_lock.rfid.RFIDReader") as mock:
        mock_reader = MagicMock()
        mock.return_value = mock_reader
        yield mock_reader


@pytest.fixture
def mock_simple_mfrc522() -> Generator[MagicMock, None, None]:
    """Fixture to mock SimpleMFRC522."""
    with patch("rfid_servo_lock.rfid.SimpleMFRC522") as mock:
        mock_reader = MagicMock()
        mock.return_value = mock_reader
        yield mock_reader


@pytest.fixture
def mock_gpio() -> Generator[MagicMock, None, None]:
    """Fixture to mock GPIO module."""
    with patch("rfid_servo_lock.rfid.GPIO") as mock:
        yield mock


class TestRFIDReader:
    """Unit tests for the RFIDReader class."""

    def test_init(self, mock_simple_mfrc522: MagicMock) -> None:
        """Test RFIDReader initialization."""
        rfid_reader = RFIDReader()

        assert rfid_reader.reader is not None
        assert mock_simple_mfrc522 is not None

    def test_read_card_success(self, mock_simple_mfrc522: MagicMock) -> None:
        """Test successful card reading."""
        expected_card_id = 123456789
        expected_text = "test_password"
        mock_simple_mfrc522.read.return_value = (expected_card_id, expected_text)

        rfid_reader = RFIDReader()
        result = rfid_reader.read_card()

        mock_simple_mfrc522.read.assert_called_once()
        assert result == (expected_card_id, expected_text)

    def test_read_card_exception(self, mock_simple_mfrc522: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test card reading when an exception occurs."""
        mock_simple_mfrc522.read.side_effect = Exception("RFID read error")

        rfid_reader = RFIDReader()

        with caplog.at_level(logging.ERROR):
            result = rfid_reader.read_card()

        assert result is None
        assert "Error reading card!" in caplog.text
        mock_simple_mfrc522.read.assert_called_once()

    def test_write_card_success(self, mock_simple_mfrc522: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test successful card writing."""
        test_text = "test_password"

        rfid_reader = RFIDReader()

        with caplog.at_level(logging.INFO):
            result = rfid_reader.write_card(test_text)

        mock_simple_mfrc522.write.assert_called_once_with(test_text)
        assert result is True
        assert "Data writing is complete" in caplog.text

    def test_write_card_exception(self, mock_simple_mfrc522: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test card writing when an exception occurs."""
        test_text = "test_password"
        mock_simple_mfrc522.write.side_effect = Exception("RFID write error")

        rfid_reader = RFIDReader()

        with caplog.at_level(logging.ERROR):
            result = rfid_reader.write_card(test_text)

        assert result is False
        assert "Error writing to card!" in caplog.text
        mock_simple_mfrc522.write.assert_called_once_with(test_text)

    @pytest.mark.parametrize(
        ("card_id", "text"),
        [
            (987654321, "password123"),
            (555555555, "secret_key"),
            (111111111, ""),
            (999999999, "very_long_password_text_that_might_be_stored_on_card"),
        ],
    )
    def test_read_card_various_data(self, mock_simple_mfrc522: MagicMock, card_id: int, text: str) -> None:
        """Test reading cards with various data combinations."""
        mock_simple_mfrc522.read.return_value = (card_id, text)

        rfid_reader = RFIDReader()
        result = rfid_reader.read_card()

        assert result == (card_id, text)
        mock_simple_mfrc522.read.assert_called_once()

    @pytest.mark.parametrize(
        "test_text",
        [
            "simple_password",
            "password_with_123_numbers",
            "",
            "special_chars_!@#$%^&*()",
            "a" * 100,
        ],
    )
    def test_write_card_various_text(self, mock_simple_mfrc522: MagicMock, test_text: str) -> None:
        """Test writing various types of text to cards."""
        rfid_reader = RFIDReader()
        result = rfid_reader.write_card(test_text)

        assert result is True
        mock_simple_mfrc522.write.assert_called_once_with(test_text)


class TestReadFunction:
    """Unit tests for the read function."""

    def test_read_successful_card_detection(
        self, mock_rfid_reader: MagicMock, mock_sleep: MagicMock, mock_gpio: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test read function with successful card detection."""
        mock_rfid_reader.read_card.side_effect = [(123456789, "test_password"), KeyboardInterrupt()]

        with caplog.at_level(logging.INFO):
            read()

        assert mock_rfid_reader.read_card.call_count == 1 + 1
        assert "Place the card on the reader..." in caplog.text
        assert "Text: test_password" in caplog.text
        assert "Exiting..." in caplog.text
        assert "Cleanup complete." in caplog.text
        mock_sleep.assert_called_with(3)
        mock_gpio.cleanup.assert_called_once()

    def test_read_failed_card_detection(
        self, mock_rfid_reader: MagicMock, mock_sleep: MagicMock, mock_gpio: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test read function when card detection fails."""
        mock_rfid_reader.read_card.side_effect = [None, KeyboardInterrupt()]

        with caplog.at_level(logging.INFO):
            read()

        assert mock_rfid_reader.read_card.call_count == 1 + 1
        assert "Place the card on the reader..." in caplog.text
        assert "Text:" not in caplog.text
        assert "Exiting..." in caplog.text
        assert "Cleanup complete." in caplog.text
        mock_sleep.assert_called_with(3)
        mock_gpio.cleanup.assert_called_once()

    def test_read_immediate_keyboard_interrupt(
        self, mock_rfid_reader: MagicMock, mock_sleep: MagicMock, mock_gpio: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test read function with immediate KeyboardInterrupt."""
        mock_rfid_reader.read_card.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.INFO):
            read()

        assert mock_rfid_reader.read_card.call_count == 1
        assert "Place the card on the reader..." in caplog.text
        assert "Text:" not in caplog.text
        assert "Exiting..." in caplog.text
        assert "Cleanup complete." in caplog.text
        mock_sleep.assert_not_called()
        mock_gpio.cleanup.assert_called_once()


class TestWriteFunction:
    """Unit tests for the write function."""

    @pytest.fixture
    def mock_input(self) -> Generator[MagicMock, None, None]:
        """Fixture to mock builtins.input."""
        with patch("builtins.input") as mock:
            yield mock

    @pytest.fixture
    def mock_save_authorized_card(self) -> Generator[MagicMock, None, None]:
        """Fixture to mock save_authorized_card function."""
        with patch("rfid_servo_lock.rfid.save_authorized_card") as mock:
            yield mock

    def test_write_successful_single_card(
        self,
        mock_input: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_save_authorized_card: MagicMock,
        mock_gpio: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test write function with successful single card operation."""
        mock_input.side_effect = ["testpassword", "quit"]
        mock_rfid_reader.read_card.return_value = (123456789, "")
        mock_rfid_reader.write_card.return_value = True

        with caplog.at_level(logging.INFO):
            write()

        assert mock_input.call_count == 1 + 1
        mock_input.assert_any_call("Enter password for RFID card (or 'quit' to exit): ")
        mock_rfid_reader.read_card.assert_called_once()
        mock_save_authorized_card.assert_called_once_with(123456789, "testpassword")
        mock_rfid_reader.write_card.assert_called_once_with("testpassword")
        assert "Place the card on the reader..." in caplog.text
        assert "Password hash saved for card 123456789" in caplog.text
        assert "Card 123456789 is now authorized for the lock system." in caplog.text
        assert "Cleanup complete." in caplog.text
        mock_gpio.cleanup.assert_called_once()

    @pytest.mark.parametrize("quit_cmd", ["quit", "q", "exit"])
    def test_write_quit_variations(
        self,
        quit_cmd: str,
        mock_input: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_gpio: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test write function with different quit command variations."""
        mock_input.side_effect = [quit_cmd]

        with caplog.at_level(logging.INFO):
            write()

        mock_rfid_reader.read_card.assert_not_called()
        mock_rfid_reader.write_card.assert_not_called()
        mock_gpio.cleanup.assert_called_once()

    def test_write_empty_password(
        self,
        mock_input: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_gpio: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test write function with empty password."""
        mock_input.side_effect = ["", "quit"]

        with caplog.at_level(logging.ERROR):
            write()

        assert "Password cannot be empty!" in caplog.text
        mock_rfid_reader.read_card.assert_not_called()
        mock_rfid_reader.write_card.assert_not_called()
        mock_gpio.cleanup.assert_called_once()

    def test_write_card_read_failure(
        self,
        mock_input: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_gpio: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test write function when card reading fails."""
        mock_input.side_effect = ["testpassword", "quit"]
        mock_rfid_reader.read_card.return_value = None

        with caplog.at_level(logging.ERROR):
            write()

        assert "Failed to read card ID!" in caplog.text
        mock_rfid_reader.read_card.assert_called_once()
        mock_rfid_reader.write_card.assert_not_called()
        mock_gpio.cleanup.assert_called_once()

    def test_write_save_authorized_card_failure(
        self,
        mock_input: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_save_authorized_card: MagicMock,
        mock_gpio: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test write function when saving authorized card fails."""
        mock_input.side_effect = ["testpassword", "quit"]
        mock_rfid_reader.read_card.return_value = (123456789, "")
        mock_save_authorized_card.side_effect = Exception("Save failed")

        with caplog.at_level(logging.ERROR):
            write()

        assert "Failed to save password hash" in caplog.text
        mock_rfid_reader.read_card.assert_called_once()
        mock_rfid_reader.write_card.assert_called_once_with("testpassword")
        mock_save_authorized_card.assert_called_once_with(123456789, "testpassword")
        mock_gpio.cleanup.assert_called_once()

    def test_write_card_write_failure(
        self,
        mock_input: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_save_authorized_card: MagicMock,
        mock_gpio: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test write function when card writing fails."""
        mock_input.side_effect = ["testpassword", "quit"]
        mock_rfid_reader.read_card.return_value = (123456789, "")
        mock_rfid_reader.write_card.return_value = False

        with caplog.at_level(logging.ERROR):
            write()

        assert "Failed to write password to card!" in caplog.text
        mock_rfid_reader.read_card.assert_called_once()
        mock_rfid_reader.write_card.assert_called_once_with("testpassword")
        mock_save_authorized_card.assert_called_once_with(123456789, "testpassword")
        mock_gpio.cleanup.assert_called_once()

    def test_write_keyboard_interrupt(
        self,
        mock_input: MagicMock,
        mock_rfid_reader: MagicMock,
        mock_gpio: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test write function handles KeyboardInterrupt."""
        mock_input.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.INFO):
            write()

        assert "Exiting..." in caplog.text
        assert "Cleanup complete." in caplog.text
        mock_rfid_reader.read_card.assert_not_called()
        mock_rfid_reader.write_card.assert_not_called()
        mock_gpio.cleanup.assert_called_once()
