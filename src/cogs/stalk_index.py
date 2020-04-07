import logging
import discord
import json
import os
import datetime
from discord.ext import commands, tasks
from discord.ext.commands import Context


class StalkIndex(commands.Cog):

    _MIN_TURNIP_PRICE = 1
    _MAX_TURNIP_PRICE = 600
    _LOG_PREFIX = 'week_'
    _LOG_EXT_TYPE = '.json'
    _DAYS_OF_THE_WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    def __init__(self, client: commands.Bot):
        self._client = client
        try:
            self.update_local_all_channels()
            #with open('channels.json', 'r') as file:
            #    self._all_channels = json.load(file)
        except json.JSONDecodeError as error:
            with open('channels.json', 'w+') as file:
                file.write("{}")
            self._all_channels = {}

    def update_local_all_channels(self):
        with open('channels.json', 'r') as file:
            self._all_channels = json.load(file)

    def get_log_name_for_date(self, date: datetime.date) -> str:
        week_number = date.isocalendar()[1]
        return self._LOG_PREFIX + str(week_number) + self._LOG_EXT_TYPE

    # EVENTS IN COGS; analogue to @client.event decorator
    @commands.Cog.listener()
    async def on_ready(self):
        await self._client.change_presence(status=discord.Status.online, activity=discord.Game('Stalk Market'))
        logging.info("Stalk Index is ready")

    @commands.command(aliases=['add'])
    async def add_stalk_channel(self, context: Context, channel: discord.TextChannel):
        with open('channels.json', 'r') as file:
            all_channels = json.load(file)
        guild_id = str(context.guild.id)
        if guild_id not in all_channels:
            all_channels[guild_id] = []
        channel_id = str(channel.id)
        if channel_id in all_channels[guild_id]:
            await context.send(f'The Stalk Index is already listening to #**{channel}**!')
        else:
            all_channels[guild_id].append(str(channel.id))
            with open('channels.json', 'w') as file:
                json.dump(all_channels, file, indent=4)
            self.update_local_all_channels()
            await context.send(f'The Stalk Index will begin listening to stalk prices on #**{channel}**!')

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
        with open('channels.json', 'r') as file:
            all_channels = json.load(file)
        guild_id = str(context.guild.id)
        if guild_id not in all_channels:
            all_channels[guild_id] = []
        channel_id = str(channel.id)
        if channel_id in all_channels[guild_id]:
            all_channels[guild_id].remove(channel_id)
            with open('channels.json', 'w') as file:
                json.dump(all_channels, file, indent=4)
            await context.send(f'The Stalk Index will stop listening to stalk prices on #**{channel}**.')
            self.update_local_all_channels()
        else:
            await context.send(f'The Stalk Index is not currently listening to #**{channel}**!')

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
        #with open('channels.json', 'r') as file:
        #    all_channels = json.load(file)
        guild_id = str(context.guild.id)
        #if guild_id not in all_channels:
        #    all_channels[guild_id] = []

        msg = 'The Stalk Index is currently listening to the following channels:\n'
        for channel_name in [self._client.get_channel(int(channel_id)).name for channel_id in self._all_channels[guild_id]]:
            msg += f'\t#**{channel_name}**\n'

        await context.send(msg)

    def attempt_to_set_user_turnip_price(self, user_id: str, local_datetime: datetime, value: int, overwrite: bool):
        file_name = self.get_log_name_for_date(local_datetime.date())
        file_path = os.path.abspath(os.path.join('logs', file_name))
        if not os.path.exists(file_path):
            with open(file_path, 'w+') as file:
                file.write('{}')
        with open(os.path.join('logs', file_name), 'r') as file:
            try:
                users = json.load(file)
            except json.JSONDecodeError as decode_error:
                users = {}
        if user_id not in users:
            users[user_id] = {"monday": {"am": 0, "pm": 0},
                              "tuesday": {"am": 0, "pm": 0},
                              "wednesday": {"am": 0, "pm": 0},
                              "thursday": {"am": 0, "pm": 0},
                              "friday": {"am": 0, "pm": 0},
                              "saturday": {"am": 0, "pm": 0},
                              "sunday": {"am": 0, "pm": 0}}

        day_of_the_week = self._DAYS_OF_THE_WEEK[local_datetime.weekday()]
        if local_datetime.hour >= 12:
            time_of_day = "pm"
        else:
            time_of_day = "am"

        if not overwrite and users[user_id][day_of_the_week][time_of_day] != 0:
            return f"your turnip price was already set for {day_of_the_week} ({time_of_day}) to {users[user_id][day_of_the_week][time_of_day]} bells. Use !{value} to force overwrite."

        users[user_id][day_of_the_week][time_of_day] = value

        with open(file_path, 'w') as file:
            json.dump(users, file)

        return None

    @commands.command()
    async def report(self, context: Context):
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


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        if message.author.bot:
            return  # that's a bot!

        if channel_id in self._all_channels[guild_id]:
            lines = message.content.split(' ')
            if len(lines) > 0:
                force_overwrite = False
                str_value = lines[0].lower().lstrip().rstrip()
                if lines[0][0] == '!':
                    force_overwrite = True
                    str_value = str_value[1:]
                value = None
                try:
                    value = int(str_value)
                except ValueError as value_error:
                    pass
                if value is not None:
                    if self._MIN_TURNIP_PRICE <= value <= self._MAX_TURNIP_PRICE:
                        response = self.attempt_to_set_user_turnip_price(str(message.author.id), message.created_at, value, force_overwrite)
                        if response is None:
                            await message.add_reaction('👍')
                        else:
                            await message.channel.send(f"**{message.author}**, {response}")
                    else:
                        await message.channel.send(f"**{message.author}**, your Turnip sell price must be between {self._MIN_TURNIP_PRICE} and {self._MAX_TURNIP_PRICE} bells!")
                        await message.add_reaction('💩')


# setup function to attach to bot
def setup(client):
    client.add_cog(StalkIndex(client))
