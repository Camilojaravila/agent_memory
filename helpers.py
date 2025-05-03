import datetime
from zoneinfo import ZoneInfo

def time_now():
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
    return bogota_now.isoformat()