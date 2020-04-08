import os
import json
import typing

_CONFIG_DIRECTORY = os.path.abspath('.\DataStore\guild_config')
_CONFIG_PREFIX = 'CFG_'
_CONFIG_EXT = '.json'
_CHANNEL_LISTENING_ID = "Listened Channels"

_DEFAULT_SERVER_CONFIG = {_CHANNEL_LISTENING_ID: []}


def verify_config(config_path: str):
    dirname = os.path.dirname(config_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if not os.path.exists(config_path):
        with open(config_path, 'w') as file:
            json.dump(_DEFAULT_SERVER_CONFIG, file, indent=4)
    with open(config_path, 'r+') as file:
        if file.read() == '':
            file.seek(0)
            json.dump(_DEFAULT_SERVER_CONFIG, file, indent=4)
            return
    with open(config_path, 'r') as file:
        try:
            _ = json.load(file)
        except json.JSONDecodeError as decode_err:
            raise ValueError(f"Config JSON was not empty, but was not valid. Get some human eyes on {config_path}!")


def get_config_name(guild_id: str) -> str:
    return _CONFIG_PREFIX + guild_id + _CONFIG_EXT


def get_verified_config_path(guild_id: str) -> str:
    config_path = os.path.join(_CONFIG_DIRECTORY, get_config_name(guild_id))
    verify_config(config_path)
    return config_path


def add_listening_channel(channel_id: str, guild_id: str):
    config_path = get_verified_config_path(guild_id)
    with open(config_path, 'r') as file:
        config = json.load(file)
    config[_CHANNEL_LISTENING_ID].append(channel_id)
    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)


def remove_listening_channel(channel_id: str, guild_id: str):
    config_path = get_verified_config_path(guild_id)
    with open(config_path, 'r') as file:
        config = json.load(file)
    config[_CHANNEL_LISTENING_ID].remove(channel_id)
    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)


def is_listening_to_channel(channel_id: str, guild_id: str):
    with open(get_verified_config_path(guild_id), 'r') as file:
        listening_channels = json.load(file)[_CHANNEL_LISTENING_ID]
        if channel_id in listening_channels:
            return True
        else:
            return False


def get_listening_channels(guild_id: str) -> typing.List[str]:
    with open(get_verified_config_path(guild_id), 'r') as file:
        return json.load(file)[_CHANNEL_LISTENING_ID]
