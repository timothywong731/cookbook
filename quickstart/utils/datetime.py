from datetime import datetime


def format_datetime(dt: datetime) -> str:
    """
    Format a datetime object into a string in the format 'YYYY-MM-DD HH:MM:SS'.

    Args:
        dt (datetime): The datetime object to format.

    Returns:
        str: The formatted datetime string.
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")
