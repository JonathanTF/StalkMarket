import datetime
import os
import json
import typing
import pytz
import datetime


_LOGS_DIRECTORY = os.path.abspath('./DataStore/user_config')
_LOG_PREFIX = 'USR_'
_LOG_EXT_TYPE = '.json'
_DEFAULT_LOG = {"timezone": "US/Central"}


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


def get_log_name(user_id: str) -> str:
    return _LOG_PREFIX + user_id + _LOG_EXT_TYPE


def get_verified_log_path(user_id) -> str:
    log_path = os.path.join(_LOGS_DIRECTORY, get_log_name(user_id))
    verify_log(log_path)
    return log_path


def verify_user_data(user_id: str, user_data: typing.Dict):
    if "timezone" not in user_data:
        user_data["timezone"] = "US/Central"


def get_user_timezone(user_id: str) -> str:
    with open(get_verified_log_path(user_id), 'r') as file:
        user_config = json.load(file)
    verify_user_data(user_id, user_config)
    return user_config['timezone']


def set_user_timezone(user_id: str, timezone: str):
    with open(get_verified_log_path(user_id), 'r') as file:
        user_config = json.load(file)
    verify_user_data(user_id, user_config)
    user_config['timezone'] = timezone
    with open(get_verified_log_path(user_id), 'w+') as file:
        json.dump(user_config, file, indent=4)

