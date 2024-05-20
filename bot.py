import json
import logging
import asyncio
import websockets
import discord
from discord.ext import commands, tasks
from datetime import datetime, time

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
		self.redirect_uri = config['redirect_uri']
		self.channels = config['channels']
		self.websocket_url = config['websocket_url']
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
				"websocket_url": self.websocket_url,
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

		# Here we are Checking the rate limit
		now = datetime.now()
		time_since_last_message = (now - self.last_message_time[channel_id]).total_seconds()
		if self.message_counters[channel_id] >= rate_limit and time_since_last_message < rate_limit_interval:
			return False

		# Here we are Checking the time constraints
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

# Here we are connecting to the web socket 
class WebSocketClient:
	def __init__(self, url, message_handler):
		self.url = url
		self.message_handler = message_handler
		self.connected = False

	async def connect(self):
		try:
			async with websockets.connect(self.url) as websocket:
				self.connected = True
				async for message in websocket:
					await self.message_handler(message)
		except Exception as e:
			logging.error(f"WebSocket connection error: {e}")
			self.connected = False

class MessageBot(commands.Cog):
	def __init__(self, bot, channel_manager, websocket_client):
		self.bot = bot
		self.channel_manager = channel_manager
		self.websocket_client = websocket_client

	@commands.Cog.listener()
	async def on_ready(self):
		logging.info(f'Logged in as {self.bot.user.name}')
		self.reset_message_counters.start()
		await self.websocket_client.connect()

	@commands.command()
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def get_history(self, ctx, limit: int = 10):
		channel = ctx.channel
		messages = await channel.history(limit=limit).flatten()
		history = "\n".join([f"{msg.author}: {msg.content}" for msg in messages])
		await ctx.send(f"Last {limit} messages:\n{history}")

	@commands.command()
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def subscribe(self, ctx, signal: str):
		channel_id = str(ctx.channel.id)
		self.channel_manager.subscribe(channel_id, signal)
		await ctx.send(f"Subscribed to signal: {signal}")
		self.bot.config.save_config()

	@commands.command()
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def unsubscribe(self, ctx, signal: str):
		channel_id = str(ctx.channel.id)
		self.channel_manager.unsubscribe(channel_id, signal)
		await ctx.send(f"Unsubscribed from signal: {signal}")
		self.bot.config.save_config()

	@commands.command()
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def list_subscriptions(self, ctx):
		channel_id = str(ctx.channel.id)
		subscriptions = self.channel_manager.list_subscriptions(channel_id)
		if subscriptions:
			await ctx.send(f"Subscriptions: {', '.join(subscriptions)}")
		else:
			await ctx.send("No subscriptions found.")

	@commands.command()
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def rate_limits(self, ctx):
		channel_id = str(ctx.channel.id)
		config = self.channel_manager.channels.get(channel_id, {})
		rate_limit = config.get('rate_limit', 'N/A')
		rate_limit_interval = config.get('rate_limit_interval', 'N/A')
		await ctx.send(f"Rate Limit: {rate_limit}, Interval: {rate_limit_interval} seconds")

    # These are the bot commands 
	@commands.command()
	async def help(self, ctx, lang: str = "en"):
		help_messages = {
			"en": (
				"**Bot Commands:**\n"
				"`!get_history [limit]` - Get message history\n"
				"`!subscribe [signal]` - Subscribe to a signal\n"
				"`!unsubscribe [signal]` - Unsubscribe from a signal\n"
				"`!list_subscriptions` - List all subscriptions\n"
				"`!rate_limits` - View rate limits\n"
				"`!help [lang]` - Show this help message"
			),
			"es": (
				"**Comandos del Bot:**\n"
				"`!get_history [límite]` - Obtener historial de mensajes\n"
				"`!subscribe [señal]` - Suscribirse a una señal\n"
				"`!unsubscribe [señal]` - Cancelar suscripción a una señal\n"
				"`!list_subscriptions` - Listar todas las suscripciones\n"
				"`!rate_limits` - Ver límites de tasa\n"
				"`!help [lang]` - Mostrar este mensaje de ayuda"
			)
			# Add more languages as needed
		}
		await ctx.send(help_messages.get(lang, help_messages["en"]))

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

	@tasks.loop(minutes=5)
	async def monitor_bot(self):
		if not self.websocket_client.connected:
			logging.warning("WebSocket disconnected. Attempting to reconnect...")
			await self.websocket_client.connect()
		if not self.bot.is_ready():
			logging.warning("Bot not ready.")
		else:
			logging.info("Bot is operational.")

	async def handle_signal(self, message):
		try:
			signal_data = json.loads(message)
			signal = signal_data['signal']
			channels = self.channel_manager.get_subscriptions(signal)
			for channel_id in channels:
				if self.channel_manager.can_send_message(channel_id):
					channel = self.bot.get_channel(int(channel_id))
					if channel:
						await channel.send(f"Signal received: {signal}")
						self.channel_manager.increment_message_counter(channel_id)
		except Exception as e:
			logging.error(f"Error handling message: {e}")

	@tasks.loop(hours=24)
	async def reset_message_counters(self):
		self.channel_manager.reset_message_counters()
		logging.info("Message counters reset.")

class DiscordBot:
	def __init__(self, config_file):
		self.config = BotConfig(config_file)
		logging.basicConfig(filename=self.config.log_file, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
		self.bot = commands.Bot(command_prefix='!')
		self.bot.config = self.config
		self.channel_manager = ChannelManager(self.config.channels, self.config.subscriptions)
		self.message_bot = MessageBot(self.bot, self.channel_manager, WebSocketClient(self.config.websocket_url, self.bot.loop.create_task(self.message_bot.handle_signal)))
		self.bot.add_cog(self.message_bot)

	def run(self):
		self.bot.run(self.config.token)
		self.message_bot.monitor_bot.start()

if __name__ == '__main__':
	bot = DiscordBot('config.json')
	bot.run()
