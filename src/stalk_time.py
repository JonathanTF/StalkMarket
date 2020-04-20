from enum import IntEnum
import datetime
import typing
import pytz
from pytz import timezone


def get_week_number(date: datetime.date):
    if date.weekday() == 6:
        # for sunday, we want to report for the next week
        return (date.isocalendar()[1] + 1) % 53
    return date.isocalendar()[1]


def get_year_number(date: datetime.date):
    if date.weekday() == 6 and date.day == 31:
        # it's new year's eve on a sunday, so report sunday prices for next year
        return date.isocalendar()[0] + 1
    return date.isocalendar()[0]


def get_is_valid_timezone(tz: str) -> bool:
    try:
        return pytz.timezone(tz) is not None
    except pytz.exceptions.UnknownTimeZoneError:
        return False


def convert_timezone_str_to_tzinfo(timezone_str: str) -> datetime.tzinfo:
    return pytz.timezone(timezone_str)


def get_adjusted_time(date: datetime.datetime, tz: datetime.tzinfo) -> datetime.datetime:
    return date.astimezone(tz)


def convert_datetime_to_server_datetime(date: datetime.datetime) -> datetime.datetime:
    return date.astimezone(timezone('America/Chicago'))


class DayOfTheWeek(IntEnum):

    MONDAY = 1,
    TUESDAY = 2,
    WEDNESDAY = 3,
    THURSDAY = 4,
    FRIDAY = 5,
    SATURDAY = 6,
    SUNDAY = 0

    def __str__(self):
        return str(self.name)


class TimeOfDay(IntEnum):
    AM = 0,
    PM = 1

    def __str__(self):
        return str(self.name)


def get_day_of_the_week(date: datetime.datetime) -> DayOfTheWeek:

    weekday = (date.weekday() + 1) % 7
    return DayOfTheWeek(weekday)


def get_time_of_day(date: datetime.datetime) -> TimeOfDay:
    hour = date.hour + (date.utcoffset().total_seconds() / 3600)
    if hour >= 12:
        return TimeOfDay.PM
    else:
        return TimeOfDay.AM


def get_time_of_day_human_readable_name(time: TimeOfDay) -> str:
    if time == TimeOfDay.AM:
        return "am"
    elif time == TimeOfDay.PM:
        return "pm"
    else:
        raise ValueError(f"Unknown time of day: {time}")


def get_day_of_the_week_human_friendly_name(day: DayOfTheWeek, abbreviate: bool = False) -> str:
    if day == DayOfTheWeek.MONDAY:
        if abbreviate:
            return "mon"
        else:
            return "monday"
    elif day == DayOfTheWeek.TUESDAY:
        if abbreviate:
            return "tues"
        else:
            return "tuesday"
    elif day == DayOfTheWeek.WEDNESDAY:
        if abbreviate:
            return "wed"
        else:
            return "wednesday"
    elif day == DayOfTheWeek.THURSDAY:
        if abbreviate:
            return "thu "
        else:
            return "thursday"
    elif day == DayOfTheWeek.FRIDAY:
        if abbreviate:
            return "fri "
        else:
            return "friday"
    elif day == DayOfTheWeek.SATURDAY:
        if abbreviate:
            return "sat"
        else:
            return "saturday"
    elif day == DayOfTheWeek.SUNDAY:
        if abbreviate:
            return "sun"
        else:
            return "sunday"
    else:
        raise ValueError(f"Unknown day of the week: {day}")


def get_day_of_the_week_enum_from_human_readable_name_or_none(name: str) -> typing.Optional[DayOfTheWeek]:
    name = name.lower().lstrip().rstrip()

    for week_enum in [DayOfTheWeek.SUNDAY, DayOfTheWeek.MONDAY, DayOfTheWeek.TUESDAY, DayOfTheWeek.WEDNESDAY, DayOfTheWeek.THURSDAY, DayOfTheWeek.FRIDAY, DayOfTheWeek.SATURDAY]:
        if name == get_day_of_the_week_human_friendly_name(week_enum):
            return week_enum

    return None


def get_time_of_day_enum_from_human_readable_name_or_none(name: str) -> typing.Optional[TimeOfDay]:
    name = name.lower().lstrip().rstrip()

    for time_enum in [TimeOfDay.AM, TimeOfDay.PM]:
        if name == get_time_of_day_human_readable_name(time_enum):
            return time_enum

    return None


