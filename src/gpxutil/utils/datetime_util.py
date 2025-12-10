import datetime


def datetime_yyyymmdd_slash_time_microsecond_tz(date_str: str, time_str: str, microsecond: int = 0, timezone: datetime.timezone = datetime.timezone.utc) -> datetime.datetime:
    """
    根据日期（YYYY/mm/dd）、时间（'HH:MM:SS'）、毫秒、时区，给出 datetime 对象。
    """
    date = datetime.datetime.strptime(date_str + ' ' + time_str, '%Y/%m/%d %H:%M:%S')
    # date 添加 microsecond 和时区
    date = date + datetime.timedelta(microseconds=microsecond)
    date = date.replace(tzinfo=timezone)
    return date

def datetime_yyyymmdd_slash_time_to_iso(date_str: str, time_str: str, microsecond: int = 0, timezone: datetime.timezone = datetime.timezone.utc) -> str:
    """
    根据日期（YYYY/mm/dd）、时间（'HH:MM:SS'）、毫秒、时区，转换为 ISO 格式的日期字符串
    """
    return datetime_yyyymmdd_slash_time_microsecond_tz(date_str, time_str, microsecond, timezone).isoformat()

if __name__ == '__main__':
    a = datetime_yyyymmdd_slash_time_to_iso('2023/4/15', '3:33:34', 13)
    print(a)