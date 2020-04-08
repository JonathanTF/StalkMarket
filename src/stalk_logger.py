import datetime
import os
import json
import typing

from src.stalk_time import DayOfTheWeek, TimeOfDay, get_week_number, get_year_number

_LOGS_DIRECTORY = os.path.abspath('./DataStore/stalk_logs')
_LOG_PREFIX = 'STLK_'
_LOG_EXT_TYPE = '.json'
_DEFAULT_LOG = {}


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


def get_log_name(week_number: int, year_number: int) -> str:
    return _LOG_PREFIX + str(year_number) + '_' + str(week_number) + _LOG_EXT_TYPE


def get_verified_log_path(week_number: int, year_number: int) -> str:
    log_path = os.path.join(_LOGS_DIRECTORY, get_log_name(week_number, year_number))
    verify_log(log_path)
    return log_path


def get_log_name_for_date(date: datetime.date) -> str:
    week_number = get_week_number(date)
    year_number = get_year_number(date)
    return get_log_name(week_number, year_number)


def verify_user_data(user_id: str, all_user_data: typing.Dict):
    if user_id not in all_user_data:
        all_user_data[user_id] = {
            str(DayOfTheWeek.MONDAY): {str(TimeOfDay.AM): 0, str(TimeOfDay.PM): 0},
            str(DayOfTheWeek.TUESDAY): {str(TimeOfDay.AM): 0, str(TimeOfDay.PM): 0},
            str(DayOfTheWeek.WEDNESDAY): {str(TimeOfDay.AM): 0, str(TimeOfDay.PM): 0},
            str(DayOfTheWeek.THURSDAY): {str(TimeOfDay.AM): 0, str(TimeOfDay.PM): 0},
            str(DayOfTheWeek.FRIDAY): {str(TimeOfDay.AM): 0, str(TimeOfDay.PM): 0},
            str(DayOfTheWeek.SATURDAY): {str(TimeOfDay.AM): 0, str(TimeOfDay.PM): 0},
            str(DayOfTheWeek.SUNDAY): {str(TimeOfDay.AM): 0, str(TimeOfDay.PM): 0}
        }


def set_turnip_price(user_id: str, price: int, day_of_the_week: DayOfTheWeek, time_of_day: TimeOfDay, week_number: int, year_number: int):
    with open(get_verified_log_path(week_number, year_number), 'r') as file:
        all_user_turnip_prices = json.load(file)
    verify_user_data(user_id, all_user_turnip_prices)
    all_user_turnip_prices[user_id][str(day_of_the_week)][str(time_of_day)] = price
    with open(get_verified_log_path(week_number, year_number), 'w+') as file:
        json.dump(all_user_turnip_prices, file, indent=4)


def get_turnip_price(user_id: str, day_of_the_week: DayOfTheWeek, time_of_day: TimeOfDay, week_number: int, year_number: int):
    with open(get_verified_log_path(week_number, year_number), 'r') as file:
        all_user_turnip_prices = json.load(file)
    verify_user_data(user_id, all_user_turnip_prices)
    return all_user_turnip_prices[user_id][str(day_of_the_week)][str(time_of_day)]
