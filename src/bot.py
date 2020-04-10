import discord
from discord.ext import commands, tasks
import random
import os
from itertools import cycle

client = commands.Bot(command_prefix='.')


@client.command()
async def load(ctx, extension):
    """
    Loads the provided extension

    :param ctx:
    :param extension:
    :return:
    """
    client.load_extension(f'cogs.{extension}') # will go into cogs folder and load extension (example.py, for example)


@client.command()
async def unload(ctx, extension):
    """
    Unloads the provided extension

    :param ctx:
    :param extension:
    :return:
    """
    client.unload_extension(f'cogs.{extension}')


@client.event
async def on_ready():
    """
    When the bot is ready - it's got all the info it needs from discord
    :return:
    """
    print('Bot is ready.')


@client.command()
async def reload(ctx, extension):
    """
    reloads the given extension

    :param ctx:
    :param extension:
    :return:
    """
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')


# load all cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

with open('..\\.key', 'r') as file:
    token = file.read()

client.run(token)
print('hullo!')