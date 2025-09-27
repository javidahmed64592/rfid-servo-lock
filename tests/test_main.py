"""Unit tests for the main module."""

from unittest.mock import Mock, patch

import pytest

from rfid_servo_lock.main import main


@patch("rfid_servo_lock.main.RFIDReader")
@patch("rfid_servo_lock.main.ServoLock")
def test_main_initialization(mock_servo_class: Mock, mock_rfid_class: Mock) -> None:
    """Test that main initializes components correctly."""
    # Mock the instances
    mock_rfid = Mock()
    mock_servo = Mock()
    mock_rfid_class.return_value = mock_rfid
    mock_servo_class.return_value = mock_servo

    # Mock wait_for_card to return None (no card detected) and trigger KeyboardInterrupt
    mock_rfid.wait_for_card.side_effect = [None, KeyboardInterrupt()]

    # Run main function
    main()

    # Verify initialization calls
    mock_rfid_class.assert_called_once()
    mock_servo_class.assert_called_once_with(
        pin=18,
        locked_angle=0,
        unlocked_angle=90,
    )

    # Verify cleanup calls
    mock_servo.cleanup.assert_called_once()
    mock_rfid.cleanup.assert_called_once()


@patch("rfid_servo_lock.main.RFIDReader")
@patch("rfid_servo_lock.main.ServoLock")
def test_main_rfid_detection(mock_servo_class: Mock, mock_rfid_class: Mock) -> None:
    """Test that main handles RFID card detection correctly."""
    # Mock the instances
    mock_rfid = Mock()
    mock_servo = Mock()
    mock_rfid_class.return_value = mock_rfid
    mock_servo_class.return_value = mock_servo

    # Mock card detection followed by KeyboardInterrupt
    mock_rfid.wait_for_card.side_effect = [
        (123456, "test data"),  # Card detected
        KeyboardInterrupt(),  # Exit
    ]

    # Run main function
    main()

    # Verify toggle was called when card was detected
    mock_servo.toggle.assert_called_once()
