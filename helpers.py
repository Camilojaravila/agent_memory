import datetime
from zoneinfo import ZoneInfo
import re

def _time_now():
    """
    Gets the current time in Bogota, Colombia, without using pytz.

    Returns:
        datetime.datetime: The current time in Bogota.
    """
    # Get the current UTC time.
    utc_now = datetime.datetime.now(datetime.timezone.utc)

    # Define the Bogota timezone using zoneinfo.
    bogota_timezone = ZoneInfo("America/Bogota")

    # Convert the UTC time to Bogota time.
    bogota_now = utc_now.astimezone(bogota_timezone)
    return bogota_now
    
def time_now():
    return _time_now().isoformat()


def get_past_time(interval_str):
    """
    Returns the current time in Bogota minus the specified time interval.

    Args:
        interval_str (str): A string specifying the time interval to subtract, 
                           e.g., "24 hour", "5 day", "1 week".

    Returns:
        str: The past time in ISO format.
    """
    # Parse the interval string
    match = re.match(r'^(\d+)\s+(hour|day|week|minute|second|month|year)s?$', interval_str.lower())
    if not match:
        raise ValueError("Invalid interval format. Use something like '24 hour', '5 day', '1 week'.")
    
    amount = int(match.group(1))
    unit = match.group(2)
    
    # Get current time in Bogota as a datetime object
    now = _time_now()
    
    # Calculate the past time based on the unit
    if unit == 'minute':
        past_time = now - datetime.timedelta(minutes=amount)
    elif unit == 'hour':
        past_time = now - datetime.timedelta(hours=amount)
    elif unit == 'day':
        past_time = now - datetime.timedelta(days=amount)
    elif unit == 'week':
        past_time = now - datetime.timedelta(weeks=amount)
    elif unit == 'second':
        past_time = now - datetime.timedelta(seconds=amount)
    elif unit == 'month':
        past_time = now - datetime.timedelta(days=amount*30)  # Approximation
    elif unit == 'year':
        past_time = now - datetime.timedelta(days=amount*365)  # Approximation
    
    return past_time

