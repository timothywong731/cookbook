from datetime import datetime

from quickstart.utils.datetime import format_datetime


def test_format_datetime_standard():
    # Arrange
    dt = datetime(2023, 10, 27, 14, 30, 45)
    expected = "2023-10-27 14:30:45"

    # Act
    result = format_datetime(dt)

    # Assert
    assert result == expected


def test_format_datetime_single_digits():
    # Arrange
    dt = datetime(2023, 1, 5, 9, 5, 2)
    expected = "2023-01-05 09:05:02"

    # Act
    result = format_datetime(dt)

    # Assert
    assert result == expected
