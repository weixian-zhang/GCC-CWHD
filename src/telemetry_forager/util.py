

from datetime import datetime
import pytz

class DatetimeUtil:
    
    @staticmethod
    def to_friendly_datetime(date_time: datetime, time_zone='Asia/Singapore'):
        return date_time.astimezone(pytz.timezone(time_zone)).strftime("%a %d %b %Y %H:%M:%S")