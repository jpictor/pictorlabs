import datetime
import time
import pytz
import isodate
from django.utils.timezone import make_aware
from dateutil.parser import parse as dateutil_parse


UNIX_EPOCH = datetime.datetime(1970, 1, 1, 0, 0)
UNIX_EPOCH_UTC = datetime.datetime(1970, 1, 1, 0, 0, tzinfo=pytz.utc)


def datetime_from_isodate(iso_date_str, time_zone=None):
    if time_zone:
        tzinfo = pytz.timezone(time_zone)
    else:
        tzinfo = pytz.utc
    dt = isodate.parse_datetime(iso_date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)
    final_dt = dt.astimezone(tzinfo)
    return final_dt


def utctimestamp_from_isodate(iso_date_str):
    """
    Converts an ISO date string in UTC format to a unix time stamp (number of seconds since UTC Jan 1, 1970).
    2015-02-20T23:47:40.310Z
    """
    if not iso_date_str:
        return None
    dt = isodate.parse_datetime(iso_date_str)
    return utctimestamp_from_datetime(dt)


def utctimestamp_from_datetime(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)
    dt_utc = dt.astimezone(pytz.utc)
    time_span = dt_utc - UNIX_EPOCH_UTC
    return time_span.total_seconds()


def isodate_from_utctimestamp(utc_timestamp):
    utc_dt = datetime.datetime.utcfromtimestamp(utc_timestamp).replace(tzinfo=pytz.utc)
    return utc_dt.isoformat()


def strip_tz(dt):
    if dt.tzinfo is None:
        return dt
    try:
        dt_utc = dt.astimezone(pytz.utc)
    except ValueError as e:
        print('BAD! {}'.format(e))
        dt_utc = dt
    dt_utc = dt_utc.replace(tzinfo=None)
    return dt_utc


def utcnow_with_tz():
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def datetime_guess_from_str(x):
    """
    Tries to convert any date-time string its given into a unix-style timestamp.
    Returns timestamp as a long or None if it can't be parsed.

    @param x: some sort of date time string
    @return: unix timestamp
    """
    if x is None:
        return None

    try:
        dt = dateutil_parse(x)
    except Exception:
        dt = None

    return dt


def timestamp_guess_from_str(x):
    """
    Tries to convert any date-time string its given into a unix-style timestamp.
    Returns timestamp as a long or None if it can't be parsed.

    @param x: some sort of date time string
    @return: unix timestamp
    """
    dt = datetime_guess_from_str(x)
    if dt is None:
        return None
    return utctimestamp_from_datetime(dt)


def make_aware_safe(dt):
    try:
        return make_aware(dt)
    except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
        return pytz.utc.localize(dt, is_dst=False)


def week_start_end(day):
    day = datetime.datetime(day.year, day.month, day.day)
    day_of_week = day.weekday()
    to_beginning_of_week = datetime.timedelta(days=day_of_week)
    beginning_of_week = day - to_beginning_of_week
    to_end_of_week = datetime.timedelta(days=6 - day_of_week)
    end_of_week = day + to_end_of_week
    return beginning_of_week, end_of_week


def month_start(day):
    beginning_of_month = datetime.datetime(day.year, day.month, 1)
    return beginning_of_month


class DateHelper(object):
    def __init__(self, date):
        self.date = date
        self.date_dt = datetime.datetime(self.date.year, self.date.month, self.date.day)
        self.month_start_dt = datetime.datetime(self.date.year, self.date.month, 1)
        self.next_day = self.date + datetime.timedelta(days=1)
        self.next_day_dt = datetime.datetime(self.next_day.year, self.next_day.month, self.next_day.day)
        wk_start, wk_end = week_start_end(self.date)
        self.week_start_dt = wk_start
        self.week_end_dt = wk_end
        self.month_start_dt = month_start(self.date)


