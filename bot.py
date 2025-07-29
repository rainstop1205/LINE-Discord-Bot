import os
import asyncio
import discord
from discord.ext import commands
from aiohttp import web
from dc.commands import send_to_line
from line.webhook import create_line_webhook_app
from logger import logger

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    try:
        logger.info(f"🤖 Bot 已上線：{bot.user}")

        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        logger.info(f"✅ Slash commands 已同步：{[cmd.name for cmd in synced]}")

        # 🔍 印出所有已載入指令
        for cmd in bot.tree.get_commands():
            logger.info(f"🛠 已載入指令：{cmd.name}")

        if not hasattr(bot, "webhook_server_started"):
            app = create_line_webhook_app()
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", 8080)
            await site.start()
            logger.info("🚀 LINE webhook server 已啟動在 http://0.0.0.0:8080")
            bot.webhook_server_started = True
    except Exception as e:
        logger.exception(f"❌ on_ready 錯誤: {e}")

send_to_line.setup(bot)

if __name__ == "__main__":
    try:
        asyncio.run(bot.start(DISCORD_BOT_TOKEN))
    except Exception as e:
        logger.exception(f"❌ __main__ 錯誤: {e}")