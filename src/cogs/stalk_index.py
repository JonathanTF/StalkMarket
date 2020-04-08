import logging
import discord
import json
import os
import datetime
from discord.ext import commands, tasks
from discord.ext.commands import Context

import src.stalk_time as stlk_time
import src.stalk_channel_listening as stlk_channel_listening
import src.stalk_logger as stlk_turnip_logger


class StalkIndex(commands.Cog):

    _MIN_TURNIP_PRICE = 1
    _MAX_TURNIP_PRICE = 700
    #_LOG_PREFIX = 'week_'
    #_LOG_EXT_TYPE = '.json'
    #_DAYS_OF_THE_WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    def __init__(self, client: commands.Bot):
        self._client = client
        #try:
        #    self.update_local_all_channels()
            #with open('channels.json', 'r') as file:
            #    self._all_channels = json.load(file)
        #except json.JSONDecodeError as error:
        #    with open('channels.json', 'w+') as file:
        #        file.write("{}")
        #    self._all_channels = {}

    #def update_local_all_channels(self):
    #    with open('channels.json', 'r') as file:
    #        self._all_channels = json.load(file)

    #def get_log_name_for_date(self, date: datetime.date) -> str:
    #    week_number = date.isocalendar()[1]
    #    return self._LOG_PREFIX + str(week_number) + self._LOG_EXT_TYPE

    # EVENTS IN COGS; analogue to @client.event decorator
    @commands.Cog.listener()
    async def on_ready(self):
        await self._client.change_presence(status=discord.Status.online, activity=discord.Game('Stalk Market'))
        print("Stalk Index is ready")

    @commands.command(aliases=['add'])
    async def add_stalk_channel(self, context: Context, channel: discord.TextChannel):
        guild_id = str(context.guild.id)
        channel_id = str(channel.id)
        if stlk_channel_listening.is_listening_to_channel(channel_id, guild_id):
            await context.send(f'The Stalk Index is already listening to #**{channel}**!')
        else:
            stlk_channel_listening.add_listening_channel(channel_id, guild_id)
            await context.send(f'The Stalk Index will begin listening to stalk prices on #**{channel}**!')

        #if guild_id not in self._all_channels:
        #    self._all_channels[guild_id] = []
        #channel_id = str(channel.id)
        #if channel_id in self._all_channels[guild_id]:
        #    await context.send(f'The Stalk Index is already listening to #**{channel}**!')
        #else:
        #    self._all_channels[guild_id].append(str(channel.id))
        #    with open('channels.json', 'w') as file:
        #        json.dump(self._all_channels, file, indent=4)
        #    self.update_local_all_channels()
        #    await context.send(f'The Stalk Index will begin listening to stalk prices on #**{channel}**!')

    @add_stalk_channel.error
    async def add_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify a Text Channel to add.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Please specify a *valid* Text Channel to add.')
        else:
            print(error)

    @commands.command(aliases=['remove'])
    async def remove_stalk_channel(self, context: Context, channel: discord.TextChannel):
        guild_id = str(context.guild.id)
        channel_id = str(channel.id)
        if not stlk_channel_listening.is_listening_to_channel(channel_id, guild_id):
            await context.send(f'The Stalk Index is not currently listening to #**{channel}**!')
        else:
            stlk_channel_listening.remove_listening_channel(channel_id, guild_id)
            await context.send(f'The Stalk Index will stop listening to stalk prices on #**{channel}**.')

        #with open('channels.json', 'r') as file:
        #    all_channels = json.load(file)
        #guild_id = str(context.guild.id)
        #if guild_id not in all_channels:
        #    all_channels[guild_id] = []
        #channel_id = str(channel.id)
        #if channel_id in all_channels[guild_id]:
        #    all_channels[guild_id].remove(channel_id)
        #    with open('channels.json', 'w') as file:
        #        json.dump(all_channels, file, indent=4)
        #    await context.send(f'The Stalk Index will stop listening to stalk prices on #**{channel}**.')
        #    self.update_local_all_channels()
        #else:
        #    await context.send(f'The Stalk Index is not currently listening to #**{channel}**!')

    @remove_stalk_channel.error
    async def remove_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify a Text Channel to remove.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Please specify a *valid* Text Channel to remove.')
        else:
            print(error)

    @commands.command(aliases=['list'])
    async def list_stalk_channels(self, context: Context):
        guild_id = str(context.guild.id)
        msg = 'The Stalk Index is currently listening to the following channels:\n'
        channel_ids = stlk_channel_listening.get_listening_channels(guild_id)
        for channel_name in [self._client.get_channel(int(channel_id)).name for channel_id in channel_ids]:
            msg += f'\t#**{channel_name}**\n'


        #for channel_name in [self._client.get_channel(int(channel_id)).name for channel_id in self._all_channels[guild_id]]:
        #    msg += f'\t#**{channel_name}**\n'

        await context.send(msg)

    #def are_details_valid(self, context: Context):
    #    msg = context.message.content.split([' '])
    #    if len(msg) < 4:
    #        return False

    @staticmethod
    def user_str(user: discord.User) -> str:
        return f"**{user}**"

    @commands.command()
    async def set(self, context: Context, *, details):
        detail_split = details.split(' ')
        if len(detail_split) < 3:
            await context.message.add_reaction('❓')
            await context.send(f"@**{context.author}**, I'm missing some info! Please provide the day of the week, am/pm, and the turnip price.")
            return
        day_of_the_week = stlk_time.get_day_of_the_week_enum_from_human_readable_name_or_none(detail_split[0])
        if day_of_the_week is None:
            await context.message.add_reaction('❓')
            await context.send(f"@**{context.author}**, I don't recognize **{detail_split[0]}** as a day of the week, could you try one of these?\n\t**monday tuesday wednesday thursday friday saturday sunday**")
            return
        time_of_day = stlk_time.get_time_of_day_enum_from_human_readable_name_or_none(detail_split[1])
        if time_of_day is None:
            await context.message.add_reaction('❓')
            await context.send(
                f"@**{context.author}**, I don't recognize **{detail_split[1]}** as a time of day, could you try one of these?\n\t**am pm**")
            return
        try:
            turnip_price = int(detail_split[2])
        except ValueError as value_err:
            await context.message.add_reaction('❓')
            await context.send(
                f"@**{context.author}**, I don't recognize **{detail_split[2]}** as a number, please try entering an integer between {self._MIN_TURNIP_PRICE} and {self._MAX_TURNIP_PRICE}")
            return
        if not (self._MIN_TURNIP_PRICE <= turnip_price <= self._MAX_TURNIP_PRICE):
            await context.send(
                f"**{context.author}**, your Turnip sell price must be between {self._MIN_TURNIP_PRICE} and {self._MAX_TURNIP_PRICE} bells!")
            await context.message.add_reaction('💩')
            return
        # success!
        user_id = str(context.author.id)
        week_number = stlk_time.get_week_number(context.message.created_at.date())
        year_number = stlk_time.get_year_number(context.message.created_at.date())

        stlk_turnip_logger.set_turnip_price(user_id, turnip_price, day_of_the_week, time_of_day, week_number, year_number)
        await context.message.add_reaction('👍')


    @set.error
    async def set_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.add_reaction('❓')
            await ctx.send(f'@**{ctx.author}**, if you would like to manually **set** your turnip price, please provide the day, am/pm, and the turnip price, in that order.\n\tExample: *{self._client.command_prefix}set monday am 100*')
        else:
            print(error)
    #def attempt_to_set_user_turnip_price(self, user_id: str, local_datetime: datetime, value: int, overwrite: bool):
    #    file_name = self.get_log_name_for_date(local_datetime.date())
    #    file_path = os.path.abspath(os.path.join('logs', file_name))
    #    if not os.path.exists(file_path):
    #        with open(file_path, 'w+') as file:
    #            file.write('{}')
    #    with open(os.path.join('logs', file_name), 'r') as file:
    #        try:
    #            users = json.load(file)
    #        except json.JSONDecodeError as decode_error:
    #            users = {}
    #    if user_id not in users:
    #        users[user_id] = {"monday": {"am": 0, "pm": 0},
    #                          "tuesday": {"am": 0, "pm": 0},
    #                          "wednesday": {"am": 0, "pm": 0},
    #                          "thursday": {"am": 0, "pm": 0},
    #                          "friday": {"am": 0, "pm": 0},
    #                          "saturday": {"am": 0, "pm": 0},
    #                          "sunday": {"am": 0, "pm": 0}}#

    #    day_of_the_week = self._DAYS_OF_THE_WEEK[local_datetime.weekday()]
    #    if local_datetime.hour >= 12:
    #        time_of_day = "pm"
    #    else:
    #        time_of_day = "am"

    #    if not overwrite and users[user_id][day_of_the_week][time_of_day] != 0:
    #        return f"your turnip price was already set for {day_of_the_week} ({time_of_day}) to {users[user_id][day_of_the_week][time_of_day]} bells. Use !{value} to force overwrite."

     #   users[user_id][day_of_the_week][time_of_day] = value

     #   with open(file_path, 'w') as file:
     #       json.dump(users, file)

     #   return None

    @commands.command()
    async def report(self, context: Context):
        await context.send("Sorry, report command is currently under development!")
        return

        file_name = self.get_log_name_for_date(context.message.created_at.date())
        file_path = os.path.abspath(os.path.join('logs', file_name))
        if not os.path.exists(file_path):
            await context.send("There is no stalk index data for the current week!")
            return

        with open(os.path.join('logs', file_name), 'r') as file:
            try:
                users = json.load(file)
            except json.JSONDecodeError as decode_error:
                users = {}

        user_id = str(context.author.id)
        if user_id not in users:
            await context.send(f"**{context.author}**, you do not have any stalk index data for this week.")
            return

        report_msg = f"Report for **{context.author}**:\n"
        for day in self._DAYS_OF_THE_WEEK[:-1]:
            report_msg += f"\t{day[:3]}: {users[user_id][day]['am']}, {users[user_id][day]['pm']}\n"
        await context.send(report_msg)

    async def listened_channel_turnip_request(self, message: discord.Message):
        lines = message.content.split(' ')

        if len(lines) <= 0:
            return

        is_force_overwrite = False
        str_value = lines[0].lower().lstrip().rstrip()
        if lines[0][0] == '!':
            is_force_overwrite = True
            str_value = str_value[1:]
        value = None
        try:
            value = int(str_value)
        except ValueError as value_error:
            return
        if value is None:
            return

        if not (self._MIN_TURNIP_PRICE <= value <= self._MAX_TURNIP_PRICE):
            await message.channel.send(
                f"**{message.author}**, your Turnip sell price must be between {self._MIN_TURNIP_PRICE} and {self._MAX_TURNIP_PRICE} bells!")
            await message.add_reaction('💩')
            return

        user_id = str(message.author.id)
        week_number = stlk_time.get_week_number(message.created_at.date())
        year_number = stlk_time.get_year_number(message.created_at.date())
        day_of_the_week = stlk_time.get_day_of_the_week(message.created_at)
        time_of_day = stlk_time.get_time_of_day(message.created_at)

        previous_value = stlk_turnip_logger.get_turnip_price(user_id, day_of_the_week, time_of_day, week_number, year_number)

        if not is_force_overwrite and previous_value != 0:
            await message.channel.send(f"your turnip price was already set for {stlk_time.get_day_of_the_week_human_friendly_name(day_of_the_week)} ({stlk_time.get_time_of_day_human_readable_name(time_of_day)}) to {previous_value} bells. Use !{value} to force overwrite.")
            return

        stlk_turnip_logger.set_turnip_price(user_id, value, day_of_the_week, time_of_day, week_number, year_number)
        await message.add_reaction('👍')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        if message.author.bot:
            return  # that's a bot!

        if channel_id in stlk_channel_listening.get_listening_channels(guild_id):#  self._all_channels[guild_id]:
            # a message came over on a listened channel - try to process the message
            await self.listened_channel_turnip_request(message)

        #await self._client.process_commands(message)


# setup function to attach to bot
def setup(client):
    client.add_cog(StalkIndex(client))
