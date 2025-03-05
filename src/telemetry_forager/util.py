

from datetime import datetime

class DatetimeUtil:

    def to_friendly_datetime(self, date_time, time_zone='Asia/Singapore'):
        return date_time.timezone(time_zone).strftime("%a %d %b %Y %H:%M:%S")