import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from discord.ext import commands
import discord
import asyncio
import json

from bot import BotConfig, ChannelManager, MessageBot, DiscordBot  

class TestDiscordBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We load our config
        cls.config = {
            "token": "xxx_token",
            "client_id": "xxx_client_id",
            "client_secret": "xxx_client_secret",
            "redirect_uri": "",
            "channels": {"12345": {"signals": ["SIGNAL_1"], "rate_limit": 5, "send_times": ["00:00"], "rate_limit_interval": 60}},
            "subscriptions": {"12345": ["SIGNAL_1"]},
            "log_file": "bot.log"
        }
        with open('test_config.json', 'w') as f:
            json.dump(cls.config, f)

    def setUp(self):
        self.bot = DiscordBot('test_config.json')
        self.bot.config = BotConfig('test_config.json')
        self.bot.channel_manager = ChannelManager(self.bot.config.channels, self.bot.config.subscriptions)
        self.bot.message_bot = MessageBot(self.bot.bot, self.bot.channel_manager)

    def test_reload_config(self):
        with patch.object(BotConfig, 'load_config', return_value=None) as mock_load_config:
            ctx = MagicMock()
            ctx.send = AsyncMock()
            asyncio.run(self.bot.message_bot.reload_config(self.bot.message_bot, ctx))
            mock_load_config.assert_called_once()
            ctx.send.assert_awaited_with("Configuration reloaded.")

    def test_list_subscriptions(self):
        ctx = MagicMock()
        ctx.send = AsyncMock()
        ctx.channel.id = "12345"
        asyncio.run(self.bot.message_bot.list_subscriptions(self.bot.message_bot, ctx))
        ctx.send.assert_awaited_with("Subscriptions: SIGNAL_1")

    def test_subscribe(self):
        ctx = MagicMock()
        ctx.send = AsyncMock()
        ctx.channel.id = "12345"
        signal = "test_signal"
        asyncio.run(self.bot.message_bot.subscribe(self.bot.message_bot, ctx, signal))
        ctx.send.assert_awaited_with("Subscribed to signal: test_signal")

    def test_unsubscribe(self):
        ctx = MagicMock()
        ctx.send = AsyncMock()
        ctx.channel.id = "12345"
        signal = "test_signal"
        asyncio.run(self.bot.message_bot.unsubscribe(self.bot.message_bot, ctx, signal))
        ctx.send.assert_awaited_with("Unsubscribed from signal: test_signal")

    def test_create_text_channel(self):
        ctx = MagicMock()
        ctx.send = AsyncMock()
        ctx.guild.create_text_channel = AsyncMock(return_value=MagicMock(name='example_channel'))
        ctx.guild.channels = []

        channel_name = "example_channel"
        asyncio.run(self.bot.message_bot.create_text_channel(self.bot.message_bot, ctx, channel_name))
        ctx.guild.create_text_channel.assert_awaited_with(channel_name)
        ctx.send.assert_awaited_with(f"Text channel '{channel_name}' created.")

    @classmethod
    def tearDownClass(cls):
        import os
        os.remove('test_config.json')

if __name__ == '__main__':
    unittest.main()
