import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from logger import logger
from line.api import push_text_message_to_group

ALLOWED_PARENT_CHANNEL_ID = int(os.getenv("DISCORD_ALLOWED_PARENT_CHANNEL_ID"))

def setup(bot: commands.Bot):
    @bot.tree.command(name="stl", description="傳送訊息到 LINE 群組")
    @app_commands.describe(message="你要傳送的訊息")
    async def send_to_line(interaction: discord.Interaction, message: str):
        parent_id = getattr(interaction.channel, "parent_id", interaction.channel.id)

        if parent_id != ALLOWED_PARENT_CHANNEL_ID:
            await interaction.response.send_message(
                "🚫 嘿嘿～別亂丟訊息到其他專案的 LINE 群組啦 📵", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        sender = interaction.user.display_name
        text = f"{sender}：{message}"

        try:
            success = await asyncio.wait_for(push_text_message_to_group(text), timeout=10)
            if success:
                await interaction.followup.send(f"👤 {text}")
            else:
                await interaction.followup.send("⚠️ 發送失敗，請稍後再試～")
        except asyncio.TimeoutError:
            await interaction.followup.send("🚨 發送超時，請稍後再試！")
        except Exception as e:
            logger.exception(f"❌ 發送過程出錯：{e}")
            await interaction.followup.send("🚨 發送過程中發生錯誤，請稍後再試！")