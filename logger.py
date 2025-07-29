import logging
from logging.handlers import TimedRotatingFileHandler
import os

# 確保 logs 資料夾存在
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 建立 logger
logger = logging.getLogger("discord-to-line-bot")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

# FileHandler：每天一個 log 檔案
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, "bot.log"),
    when="midnight",
    interval=1,
    backupCount=7, # 保留檔案數
    encoding="utf-8",
    utc=False
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
file_handler.suffix = "%Y%m%d"  # 加上日期後綴 (bot.log.yyyyMMdd)

# ConsoleHandler：印到 terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# 只加一次 handler，避免重複
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)