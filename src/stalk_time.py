from enum import IntEnum
import datetime
import typing


def get_week_number(date: datetime.date):
    return date.isocalendar()[1]


def get_year_number(date: datetime.date):
    return date.isocalendar()[0]


class DayOfTheWeek(IntEnum):

    MONDAY = 0,
    TUESDAY = 1,
    WEDNESDAY = 2,
    THURSDAY = 3,
    FRIDAY = 4,
    SATURDAY = 5,
    SUNDAY = 6

    def __str__(self):
        return str(self.name)


class TimeOfDay(IntEnum):
    AM = 0,
    PM = 1

    def __str__(self):
        return str(self.name)


def get_day_of_the_week(date: datetime.datetime) -> DayOfTheWeek:
    return DayOfTheWeek(date.weekday())


def get_time_of_day(date: datetime.datetime) -> TimeOfDay:
    if date.hour >= 12:
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

    for week_enum in [DayOfTheWeek.MONDAY, DayOfTheWeek.TUESDAY, DayOfTheWeek.WEDNESDAY, DayOfTheWeek.THURSDAY, DayOfTheWeek.FRIDAY, DayOfTheWeek.SATURDAY, DayOfTheWeek.SUNDAY]:
        if name == get_day_of_the_week_human_friendly_name(week_enum):
            return week_enum

    return None


def get_time_of_day_enum_from_human_readable_name_or_none(name: str) -> typing.Optional[TimeOfDay]:
    name = name.lower().lstrip().rstrip()

    for time_enum in [TimeOfDay.AM, TimeOfDay.PM]:
        if name == get_time_of_day_human_readable_name(time_enum):
            return time_enum

    return None


