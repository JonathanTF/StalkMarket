import datetime
import os
import json
import typing

from stalk_time import DayOfTheWeek, TimeOfDay, get_week_number, get_year_number

_LOGS_DIRECTORY = os.path.abspath('./DataStore/stalk_logs')
_LOG_FOLDER_PREFIX = 'STLK_'
_LOG_PREFIX = 'USR_'
_LOG_EXT_TYPE = '.json'
_DEFAULT_LOG = {"PATTERN": "unknown"}


def verify_log(log_path: str):
    dirname = os.path.dirname(log_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if not os.path.exists(log_path):
        with open(log_path, 'w+') as file:
            json.dump(_DEFAULT_LOG, file, indent=4)
    with open(log_path, 'r+') as file:
        if file.read() == '':
            file.seek(0)
            json.dump(_DEFAULT_LOG, file, indent=4)
            return
    with open(log_path, 'r') as file:
        try:
            _ = json.load(file)
        except json.JSONDecodeError as decode_err:
            raise ValueError(f"Log JSON was not empty, but was not valid. Get some human eyes on {log_path}!")


def get_logs_directory(week_number: int, year_number: int) -> str:
    log_folder = _LOG_FOLDER_PREFIX + str(year_number) + '_' + str(week_number)
    directory = os.path.join(_LOGS_DIRECTORY, log_folder)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def get_log_name(user_id: str) -> str:
    return _LOG_PREFIX + user_id + _LOG_EXT_TYPE


def get_verified_log_path(user_id: str, week_number: int, year_number: int) -> str:
    log_dir = get_logs_directory(week_number, year_number)
    log_path = os.path.join(log_dir, get_log_name(user_id))
    verify_log(log_path)
    return log_path


def get_log_name_for_date(user_id: str, date: datetime.date) -> str:
    week_number = get_week_number(date)
    year_number = get_year_number(date)
    return get_verified_log_path(user_id, week_number, year_number)


def verify_user_data(user_data: typing.Dict):

    #for day_of_the_week in [str(DayOfTheWeek(idx)) for idx in range(int(DayOfTheWeek.MAX))]:

    #   for time_of_day in [str(TimeOfDay(idx)) for idx in range(int(TimeOfDay.MAX))]:

    for day_of_the_week in DayOfTheWeek:
        day = str(day_of_the_week)
        if day not in user_data:
            user_data[day] = {str(TimeOfDay.AM): 0, str(TimeOfDay.PM): 0}
        else:
            for time_of_day in TimeOfDay:
                time: str = str(time_of_day)
                if time not in user_data[day]:
                    user_data[day][time] = 0
    if "PATTERN" not in user_data:
        user_data["PATTERN"] = "unknown"


def set_pattern(user_id: str, pattern: str, week_number: int, year_number: int):
    with open(get_verified_log_path(user_id, week_number, year_number), 'r') as file:
        user_turnip_prices = json.load(file)
    verify_user_data(user_turnip_prices)
    user_turnip_prices["PATTERN"] = pattern
    with open(get_verified_log_path(user_id, week_number, year_number), 'w+') as file:
        json.dump(user_turnip_prices, file, indent=4)


def get_pattern(user_id: str, week_number: int, year_number: int) -> int:
    with open(get_verified_log_path(user_id, week_number, year_number), 'r') as file:
        user_turnip_prices = json.load(file)
    verify_user_data(user_turnip_prices)
    return user_turnip_prices["PATTERN"]


def set_turnip_price(user_id: str, price: int, day_of_the_week: DayOfTheWeek, time_of_day: TimeOfDay, week_number: int, year_number: int):
    with open(get_verified_log_path(user_id, week_number, year_number), 'r') as file:
        user_turnip_prices = json.load(file)
    verify_user_data(user_turnip_prices)
    user_turnip_prices[str(day_of_the_week)][str(time_of_day)] = price
    with open(get_verified_log_path(user_id, week_number, year_number), 'w+') as file:
        json.dump(user_turnip_prices, file, indent=4)


def get_turnip_price(user_id: str, day_of_the_week: DayOfTheWeek, time_of_day: TimeOfDay, week_number: int, year_number: int) -> int:
    with open(get_verified_log_path(user_id, week_number, year_number), 'r') as file:
        user_turnip_prices = json.load(file)
    verify_user_data(user_turnip_prices)
    return user_turnip_prices[str(day_of_the_week)][str(time_of_day)]


def get_week_prices_dict(user_id: str, week_number: int, year_number: int) -> typing.Dict:
    with open(get_verified_log_path(user_id, week_number, year_number), 'r') as file:
        user_turnip_prices = json.load(file)
    verify_user_data(user_turnip_prices)
    return user_turnip_prices
