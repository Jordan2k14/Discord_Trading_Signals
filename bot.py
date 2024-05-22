import json
import logging
import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import asyncio

class BotConfig:
    def __init__(self, config_file):
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        self.token = config['token']
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.redirect_uri = config.get('redirect_uri', '')
        self.channels = config['channels']
        self.subscriptions = config.get('subscriptions', {})
        self.log_file = config.get('log_file', 'bot.log')

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump({
                "token": self.token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "channels": self.channels,
                "subscriptions": self.subscriptions,
                "log_file": self.log_file
            }, f, indent=4)

class ChannelManager:
    def __init__(self, channels, subscriptions):
        self.channels = channels
        self.subscriptions = subscriptions
        self.message_counters = {channel_id: 0 for channel_id in channels}
        self.last_message_time = {channel_id: datetime.min for channel_id in channels}

    def get_channels(self):
        return self.channels

    def get_subscriptions(self, signal):
        return [channel_id for channel_id, config in self.channels.items() if signal in config['signals']]

    def can_send_message(self, channel_id):
        channel_config = self.channels[channel_id]
        rate_limit = channel_config['rate_limit']
        send_times = channel_config['send_times']
        rate_limit_interval = channel_config['rate_limit_interval']

        # Check rate limits
        now = datetime.now()
        time_since_last_message = (now - self.last_message_time[channel_id]).total_seconds()
        if self.message_counters[channel_id] >= rate_limit and time_since_last_message < rate_limit_interval:
            return False

        # Check time constraints
        current_time = now.time()
        for send_time in send_times:
            send_hour, send_minute = map(int, send_time.split(':'))
            if time(send_hour, send_minute) <= current_time:
                return True

        return False

    def increment_message_counter(self, channel_id):
        self.message_counters[channel_id] += 1
        self.last_message_time[channel_id] = datetime.now()

    def reset_message_counters(self):
        self.message_counters = {channel_id: 0 for channel_id in self.channels}
        self.last_message_time = {channel_id: datetime.min for channel_id in self.channels}

    def subscribe(self, channel_id, signal):
        if channel_id not in self.subscriptions:
            self.subscriptions[channel_id] = []
        if signal not in self.subscriptions[channel_id]:
            self.subscriptions[channel_id].append(signal)

    def unsubscribe(self, channel_id, signal):
        if channel_id in self.subscriptions and signal in self.subscriptions[channel_id]:
            self.subscriptions[channel_id].remove(signal)

    def list_subscriptions(self, channel_id):
        return self.subscriptions.get(channel_id, [])

class MessageBot(commands.Cog):
    def __init__(self, bot, channel_manager):
        self.bot = bot
        self.channel_manager = channel_manager

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f'Logged in as {self.bot.user.name}')
        print(f'Logged in as {self.bot.user.name}')
        self.reset_message_counters.start()
        logging.info('Bot is ready and reset_message_counters task started')

    @commands.command(name='help_custom')
    async def help_command(self, ctx):
        help_text = (
            "Available commands:\n"
            "!get_history [limit] - Get message history\n"
            "!subscribe [signal] - Subscribe to a signal\n"
            "!unsubscribe [signal] - Unsubscribe from a signal\n"
            "!list_subscriptions - List all subscriptions\n"
            "!rate_limits - View rate limits\n"
            "!help_custom - Show this help message\n"
            "!add_channel [channel_id] - Add a channel to bot config\n"
            "!remove_channel [channel_id] - Remove a channel from bot config\n"
            "!create_text_channel [channel_name] - Create a new text channel in the server\n"
            "!set_rate_limit [channel_id] [rate_limit] [interval] - Set rate limit for a channel\n"
            "!set_send_times [channel_id] [times...] - Set send times for a channel\n"
            "!reload_config - Reload configuration\n"
            "!save_config - Save configuration\n"
        )
        await ctx.send(help_text)
        logging.info('Help command executed')
        print('Help command executed')

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def get_history(self, ctx, limit: int = 10):
        logging.info(f'Received get_history command with limit: {limit}')
        print(f'Received get_history command with limit: {limit}')
        channel = ctx.channel
        messages = [msg async for msg in channel.history(limit=limit)]
        history = "\n".join([f"{msg.author}: {msg.content}" for msg in messages])
        await ctx.send(f"Last {limit} messages:\n{history}")
        logging.info(f'History command executed with limit: {limit}')
        print(f'History command executed with limit: {limit}')

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def subscribe(self, ctx, signal: str):
        logging.info(f'Received subscribe command for signal: {signal}')
        print(f'Received subscribe command for signal: {signal}')
        channel_id = str(ctx.channel.id)
        self.channel_manager.subscribe(channel_id, signal)
        await ctx.send(f"Subscribed to signal: {signal}")
        self.bot.config.save_config()
        logging.info(f"Subscribed to signal: {signal} in channel: {channel_id}")
        print(f"Subscribed to signal: {signal} in channel: {channel_id}")

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def unsubscribe(self, ctx, signal: str):
        logging.info(f'Received unsubscribe command for signal: {signal}')
        print(f'Received unsubscribe command for signal: {signal}')
        channel_id = str(ctx.channel.id)
        self.channel_manager.unsubscribe(channel_id, signal)
        await ctx.send(f"Unsubscribed from signal: {signal}")
        self.bot.config.save_config()
        logging.info(f"Unsubscribed from signal: {signal} in channel: {channel_id}")
        print(f"Unsubscribed from signal: {signal} in channel: {channel_id}")

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def list_subscriptions(self, ctx):
        logging.info(f'Received list_subscriptions command')
        print(f'Received list_subscriptions command')
        channel_id = str(ctx.channel.id)
        subscriptions = self.channel_manager.list_subscriptions(channel_id)
        if subscriptions:
            await ctx.send(f"Subscriptions: {', '.join(subscriptions)}")
        else:
            await ctx.send("No subscriptions found.")
        logging.info(f'List subscriptions command executed for channel: {channel_id}')
        print(f'List subscriptions command executed for channel: {channel_id}')

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def rate_limits(self, ctx):
        logging.info(f'Received rate_limits command')
        print(f'Received rate_limits command')
        channel_id = str(ctx.channel.id)
        config = self.channel_manager.channels.get(channel_id, {})
        rate_limit = config.get('rate_limit', 'N/A')
        rate_limit_interval = config.get('rate_limit_interval', 'N/A')
        await ctx.send(f"Rate Limit: {rate_limit}, Interval: {rate_limit_interval} seconds")
        logging.info(f'Rate limits command executed for channel: {channel_id}')
        print(f'Rate limits command executed for channel: {channel_id}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add_channel(self, ctx, channel_id: int):
        if str(channel_id) in self.channel_manager.channels:
            await ctx.send("Channel already exists.")
        else:
            self.channel_manager.channels[str(channel_id)] = {
                "signals": [],
                "rate_limit": 5,
                "send_times": ["00:00"],
                "rate_limit_interval": 60
            }
            self.bot.config.save_config()
            await ctx.send(f"Channel {channel_id} added.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove_channel(self, ctx, channel_id: int):
        if str(channel_id) in self.channel_manager.channels:
            del self.channel_manager.channels[str(channel_id)]
            self.bot.config.save_config()
            await ctx.send(f"Channel {channel_id} removed.")
        else:
            await ctx.send("Channel does not exist.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def create_text_channel(self, ctx, channel_name: str):
        guild = ctx.guild
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await ctx.send(f"A channel with the name '{channel_name}' already exists.")
        else:
            new_channel = await guild.create_text_channel(channel_name)
            await ctx.send(f"Text channel '{channel_name}' created.")
            logging.info(f"Text channel '{channel_name}' created.")
            print(f"Text channel '{channel_name}' created.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_rate_limit(self, ctx, channel_id: int, rate_limit: int, interval: int):
        if str(channel_id) in self.channel_manager.channels:
            self.channel_manager.channels[str(channel_id)]['rate_limit'] = rate_limit
            self.channel_manager.channels[str(channel_id)]['rate_limit_interval'] = interval
            self.bot.config.save_config()
            await ctx.send(f"Rate limit set to {rate_limit} messages per {interval} seconds for channel {channel_id}.")
        else:
            await ctx.send("Channel does not exist.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_send_times(self, ctx, channel_id: int, *times):
        if str(channel_id) in self.channel_manager.channels:
            self.channel_manager.channels[str(channel_id)]['send_times'] = list(times)
            self.bot.config.save_config()
            await ctx.send(f"Send times set for channel {channel_id}: {', '.join(times)}.")
        else:
            await ctx.send("Channel does not exist.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reload_config(self, ctx):
        self.bot.config.load_config()
        await ctx.send("Configuration reloaded.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def save_config(self, ctx):
        self.bot.config.save_config()
        await ctx.send("Configuration saved.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found.")
        else:
            await ctx.send("An error occurred while processing the command.")
        logging.error(f"Error in command {ctx.command}: {error}")
        print(f"Error in command {ctx.command}: {error}")

    @tasks.loop(hours=24)
    async def reset_message_counters(self):
        self.channel_manager.reset_message_counters()
        logging.info("Message counters reset.")
        print("Message counters reset.")

class DiscordBot:
    def __init__(self, config_file):
        self.config = BotConfig(config_file)
        logging.basicConfig(filename=self.config.log_file, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

        intents = discord.Intents.default()
        intents.message_content = True

        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.bot.config = self.config
        self.channel_manager = ChannelManager(self.config.channels, self.config.subscriptions)
        self.message_bot = MessageBot(self.bot, self.channel_manager)

    async def setup(self):
        await self.bot.add_cog(self.message_bot)
        logging.info('Cogs added to bot')
        await self.bot.start(self.config.token)

    def run(self):
        logging.info('Bot is starting...')
        asyncio.run(self.setup())

if __name__ == '__main__':
    bot = DiscordBot('config.json')
    bot.run()