import logging
import discord
import json
import os
import datetime
from discord.ext import commands, tasks
from discord.ext.commands import Context

import stalk_time as stlk_time
import stalk_channel_listening as stlk_channel_listening
import stalk_logger as stlk_turnip_logger
import stalk_predictions as stlk_predictions
import stalk_user_config as stlk_user_config

import pytz
import datetime


class StalkIndex(commands.Cog):

    _MIN_TURNIP_PRICE = 1
    _MAX_TURNIP_PRICE = 700

    def __init__(self, client: commands.Bot):
        self._client = client

    # EVENTS IN COGS; analogue to @client.event decorator
    @commands.Cog.listener()
    async def on_ready(self):
        await self._client.change_presence(status=discord.Status.online, activity=discord.Game('Stalk Market'))
        print("Stalk Index is ready")

    @commands.command()
    async def add(self, context: Context, channel: discord.TextChannel):
        """
        Start listening to a text channel. Stalk Index will automatically detect numbers in this channel and record them.

        :param context:
        :param channel:
        :return:
        """
        guild_id = str(context.guild.id)
        channel_id = str(channel.id)
        if stlk_channel_listening.is_listening_to_channel(channel_id, guild_id):
            await context.send(f'The Stalk Index is already listening to #**{channel}**!')
        else:
            stlk_channel_listening.add_listening_channel(channel_id, guild_id)
            await context.send(f'The Stalk Index will begin listening to stalk prices on #**{channel}**!')

    @add.error
    async def add_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify a Text Channel to add.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Please specify a *valid* Text Channel to add.')
        else:
            print(error)

    @commands.command()
    async def remove(self, context: Context, channel: discord.TextChannel):
        """
        Stop Stalk Index from listening to a channel. Stalk Index will still reply to commands, but won't automatically detect numbers.

        :param context:
        :param channel:
        :return:
        """
        guild_id = str(context.guild.id)
        channel_id = str(channel.id)
        if not stlk_channel_listening.is_listening_to_channel(channel_id, guild_id):
            await context.send(f'The Stalk Index is not currently listening to #**{channel}**!')
        else:
            stlk_channel_listening.remove_listening_channel(channel_id, guild_id)
            await context.send(f'The Stalk Index will stop listening to stalk prices on #**{channel}**.')

    @remove.error
    async def remove_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify a Text Channel to remove.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Please specify a *valid* Text Channel to remove.')
        else:
            print(error)

    @commands.command()
    async def list(self, context: Context):
        """
        List all the text channels that Stalk Index is currently listening to.

        :param context:
        :return:
        """
        guild_id = str(context.guild.id)
        msg = 'The Stalk Index is currently listening to the following channels:\n'
        channel_ids = stlk_channel_listening.get_listening_channels(guild_id)
        for channel_name in [self._client.get_channel(int(channel_id)).name for channel_id in channel_ids]:
            msg += f'\t#**{channel_name}**\n'

        await context.send(msg)

    @staticmethod
    def user_str(user: discord.User) -> str:
        return f"**{user}**"

    @commands.command()
    async def set(self, context: Context, *, details):
        """
        Manually set your Turnip price. Provide the day, time of day, and price, in that order. Example: monday am 102

        :param context:
        :param details:
        :return:
        """
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

    #@commands.command()
    #async def predict(self, context: Context):

    @commands.command()
    async def predict(self, context: Context, output='dm'):
        """
        Request your Stalk Futures! Stalk Index will see if there's enough data to identify a pattern in your Stalks. If it can, it will DM you with a full report, which includes predited prices.

        :param context:
        :param output:
        :return:
        """
        if output == 'channel':
            out_channel = context
        elif output == 'dm':
            out_channel = await context.author.create_dm()
        else:
            context.message.add_reaction('❓')
            await context.send(f"@**{context.author}**, I don't know where output **{output}** is, could you please use one of the following outputs?\n\t**channel**\t **dm** (*default*)")
            return

        await context.message.add_reaction('📈')
        user_id = str(context.author.id)
        week_number = stlk_time.get_week_number(context.message.created_at.date())
        year_number = stlk_time.get_year_number(context.message.created_at.date())
        users_week = stlk_turnip_logger.get_week_prices_dict(user_id, week_number, year_number)
        predictions_report = await stlk_predictions.predict(users_week)

        prediction_str = stlk_predictions.get_short_prediction_string(predictions_report)

        if len(predictions_report) > 10:
            await context.send(f"@**{context.author}**, {prediction_str}\nYour Stalk Index is currently matching {len(predictions_report)} models - please provide more data to narrow down the search!")
            return

        check_where_str = ''
        if output == 'dm':
            check_where_str = "check your DMs for a full report on your Stalk Futures!"
        elif output == 'channel':
            check_where_str = "See a full report of your Stalk Futures below."
        await context.send(f"@**{context.author}**, {prediction_str}\nYour Stalk Index matches {len(predictions_report)} models - {check_where_str}\n")

        stalk_futures_str = ''
        for prediction in stlk_predictions.predictions_list_generator(predictions_report):
            stalk_futures_str += prediction

        await out_channel.send(stalk_futures_str)
        return

    @commands.command()
    async def report(self, context: Context):
        """
        Retrieves a log of your turnip prices for the current week.

        :param context:
        :return:
        """
        user_id = str(context.author.id)
        week_number = stlk_time.get_week_number(context.message.created_at.date())
        year_number = stlk_time.get_year_number(context.message.created_at.date())
        users_week = stlk_turnip_logger.get_week_prices_dict(user_id, week_number, year_number)

        report_str = ''

        for day_of_the_week in stlk_time.DayOfTheWeek:
            report_str += f"\t{stlk_time.get_day_of_the_week_human_friendly_name(day_of_the_week, abbreviate=True)} - "
            day = str(day_of_the_week)
            for time_of_day in stlk_time.TimeOfDay:
                time = str(stlk_time.TimeOfDay(time_of_day))

                price = users_week[day][time]
                report_str += f"{stlk_time.get_time_of_day_human_readable_name(time_of_day)}:{price} "

        await context.send(f"Weekly Stalk Index for @**{context.author}**:\n{report_str}")

    @commands.command(aliases=['tz'])
    async def timezone(self, context: Context, tz):
        """
        Use this command to set your timezone to a valid TZ database name. Timezones are used for automatic number detection to log your entries to the correct field.

        :param context:
        :param tz:
        :return:
        """
        if not stlk_time.get_is_valid_timezone(tz):
            await context.send(f"@**{context.author}**, I didn't understand timezone **{tz}**, try using a *TZ database name* found here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones")
            return
        user_id = str(context.author.id)
        stlk_user_config.set_user_timezone(user_id, tz)
        await context.send(f'@**{context.author}**, your timezone has been updated to {tz}.')

    @timezone.error
    async def timezone_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.add_reaction('❓')
            await ctx.send(f'@**{ctx.author}**, to set your timezone, please enter in a valid TZ database timezone following the command.\n\tExample: *{self._client.command_prefix}timezone US/Central*')
        else:
            print(error)

    @commands.command()
    async def pattern(self, context: Context, pattern):
        """
        Retrieves information about a given pattern. Use it without arguments to get a list of valid patterns.

        :param context:
        :param pattern:
        :return:
        """
        if pattern not in stlk_predictions.get_valid_patterns():
            await context.message.add_reaction('❓')
            msg = f"@**{context.author}**, I didn't recognize **{pattern}** as a market pattern, please try one of the following:\n"
            for valid_pattern in stlk_predictions.get_valid_patterns():
                msg += f"\t**{valid_pattern}**"
            await context.send(msg)
            return

        await context.send(stlk_predictions.get_pattern_info(pattern))

    @pattern.error
    async def pattern_error(self, context: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await context.message.add_reaction('❓')
            msg = f"@**{context.author}**, please provide one of the following patterns to get more information:\n"
            for valid_pattern in stlk_predictions.get_valid_patterns():
                msg += f"\t**{valid_pattern}**"
            await context.send(msg)
            return
        else:
            print(error)


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
        user_timezone = stlk_time.convert_timezone_str_to_tzinfo(stlk_user_config.get_user_timezone(user_id))
        adjusted_time = stlk_time.get_adjusted_time(message.created_at, user_timezone)

        week_number = stlk_time.get_week_number(adjusted_time)
        year_number = stlk_time.get_year_number(adjusted_time)
        day_of_the_week = stlk_time.get_day_of_the_week(adjusted_time)
        time_of_day = stlk_time.get_time_of_day(adjusted_time)

        previous_value = stlk_turnip_logger.get_turnip_price(user_id, day_of_the_week, time_of_day, week_number, year_number)

        if not is_force_overwrite and previous_value != 0:
            await message.channel.send(f"your turnip price was already set for {stlk_time.get_day_of_the_week_human_friendly_name(day_of_the_week)} ({stlk_time.get_time_of_day_human_readable_name(time_of_day)}) to {previous_value} bells. Use !{value} to force overwrite.")
            return

        stlk_turnip_logger.set_turnip_price(user_id, value, day_of_the_week, time_of_day, week_number, year_number)
        await message.add_reaction('👍')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return # happens when the bot sends / receives DMs

        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        if message.author.bot:
            return  # that's a bot!

        if channel_id in stlk_channel_listening.get_listening_channels(guild_id):
            # a message came over on a listened channel - try to process the message
            await self.listened_channel_turnip_request(message)



# setup function to attach to bot
def setup(client):
    client.add_cog(StalkIndex(client))
