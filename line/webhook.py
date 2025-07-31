import os
import json
import aiohttp
from aiohttp import web
from line.api import get_user_display_name, download_message_content
from user_whitelist import user_prefix_whitelist
from logger import logger

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
MAX_DISCORD_FILESIZE = 8 * 1024 * 1024  # 8MB

if not DISCORD_WEBHOOK_URL:
    raise RuntimeError("Missing required environment variable: DISCORD_WEBHOOK_URL")

async def post_to_discord(payload=None, files=None):
    try:
        async with aiohttp.ClientSession() as session:
            if files:
                data = aiohttp.FormData()
                for k, v in files.items():
                    data.add_field(k, v[1], filename=v[0])
                async with session.post(DISCORD_WEBHOOK_URL, data=data) as resp:
                    if resp.status not in [200, 204]:
                        logger.error(f"⚠️ Discord post failed: {resp.status} - {await resp.text()}")
                        return False
            else:
                async with session.post(DISCORD_WEBHOOK_URL, json=payload) as resp:
                    if resp.status not in [200, 204]:
                        logger.error(f"⚠️ Discord post failed: {resp.status} - {await resp.text()}")
                        return False
        return True
    except Exception as e:
        logger.exception(f"⚠️ Discord post exception: {e}")
        return False

async def handle_text(user_id, text):
    display_name = await get_user_display_name(user_id)
    await post_to_discord({"content": f"👤 {display_name}：{text}"})

async def handle_sticker(user_id, sticker_id):
    display_name = await get_user_display_name(user_id)
    image_url = f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/ANDROID/sticker.png"
    payload = {
        "content": f"👤 {display_name}：貼圖🧸",
        "embeds": [{"image": {"url": image_url}}]
    }
    await post_to_discord(payload)

async def handle_media(user_id, message_id, media_type="image"):
    content = await download_message_content(message_id)
    if not content:
        return

    type_text = {
        "image": "圖片🖼️",
        "video": "影片🎥"
    }.get(media_type, media_type)

    display_name = await get_user_display_name(user_id)
    if len(content) > MAX_DISCORD_FILESIZE:
        await post_to_discord({"content": f"👤 {display_name}：{type_text}檔案太大啦~ (超過限制)"})
        return

    file_ext = "jpg" if media_type == "image" else "mp4"
    files = {"file": (f"{media_type}.{file_ext}", content)}
    payload = {"content": f"👤 {display_name}：{type_text}"}
    await post_to_discord(payload, files)

def create_line_webhook_app():
    app = web.Application()

    async def health(request):
        return web.Response(text="Hello, LINE Bot is running!")

    async def callback(request):
        body = await request.json()
        events = body.get("events", [])

        for event in events:
            source = event.get("source", {})
            source_type = source.get("type")

            if source_type == "group":
                logger.info(f"🟢 收到來自group的訊息，groupId：{source.get('groupId')}")
            elif source_type == "room":
                logger.info(f"🟣 收到來自room的訊息，roomId：{source.get('roomId')}")
            elif source_type == "user":
                logger.info(f"🔵 收到來自user的訊息，userId：{source.get('userId')}")

            if event.get("type") != "message":
                continue

            msg = event["message"]
            user_id = event.get("source", {}).get("userId", "(unknown)")

            match msg.get("type"):
                case "text":
                    await handle_text(user_id, msg.get("text", ""))
                case "sticker":
                    await handle_sticker(user_id, msg.get("stickerId"))
                case "image":
                    await handle_media(user_id, msg.get("id"), "image")
                case "video":
                    await handle_media(user_id, msg.get("id"), "video")
                case _:
                    logger.debug(f"🪧 Unsupported message type: {msg.get('type')}")

        return web.Response(text="OK")

    app.router.add_get("/", health)
    app.router.add_post("/callback", callback)
    return app