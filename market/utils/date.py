from datetime import datetime


def convert_datetime_to_iso_8601_with_z_suffix(dt: datetime) -> str:
    return dt.isoformat(timespec='milliseconds') + "Z"
