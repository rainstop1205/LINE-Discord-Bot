import aiohttp
import os
from logger import logger
from user_whitelist import user_prefix_whitelist

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_TARGET_GROUP_ID = os.getenv("LINE_TARGET_GROUP_ID")
MAX_DISCORD_FILESIZE = 8 * 1024 * 1024  # 8MB
user_cache = {}

if not LINE_CHANNEL_ACCESS_TOKEN:
    raise RuntimeError("❌ LINE_CHANNEL_ACCESS_TOKEN 未設定")

def get_auth_headers():
    return {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }

async def get_user_display_name(user_id):
    if user_id in user_cache:
        return user_cache[user_id]

    prefix = user_id[:6]
    if prefix in user_prefix_whitelist:
        display_name = user_prefix_whitelist[prefix]
        user_cache[user_id] = display_name
        return display_name

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.line.me/v2/bot/profile/{user_id}", headers=get_auth_headers()) as resp:
                if resp.status == 200:
                    profile = await resp.json()
                    display_name = profile.get("displayName") or f"(unknown user {prefix})"
                    user_cache[user_id] = display_name
                    return display_name
                else:
                    logger.warning(f"⚠️ 取得 LINE 使用者資料失敗：{resp.status}")
    except Exception as e:
        logger.exception(f"💥 無法取得 LINE 使用者顯示名稱：{e}")

    return f"(user {prefix})"

async def download_message_content(message_id):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api-data.line.me/v2/bot/message/{message_id}/content", headers=get_auth_headers()) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    logger.error(f"⚠️ LINE 媒體下載失敗：{resp.status}")
    except Exception as e:
        logger.exception(f"💥 下載媒體時出錯：{e}")
    return None

async def push_text_message_to_group(text: str):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": LINE_TARGET_GROUP_ID,
        "messages": [{"type": "text", "text": text}]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                text_resp = await resp.text()
                if 200 <= resp.status < 300:
                    logger.info("✅ 成功發送訊息至 LINE 群組")
                    return True
                else:
                    logger.error(f"⚠️ LINE 發送失敗：{resp.status} - {text_resp}")
                    return False
    except Exception as e:
        logger.exception(f"💥 發送 LINE 訊息時發生例外：{e}")
        return False