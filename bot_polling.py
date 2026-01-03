#!/usr/bin/env python3
import os
import tempfile
import shutil
import logging
import asyncio
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- Настройки ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
COOKIEFILE = os.getenv("COOKIEFILE")  # если приватные посты

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YTDL_OPTS = {
    "format": "bv*+ba/b",
    "merge_output_format": "mp4",
    "outtmpl": "%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
}
if COOKIEFILE:
    YTDL_OPTS["cookiefile"] = COOKIEFILE

MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB для sendVideo


# --- yt-dlp скачивание ---
def download_reel(url: str, dest_dir: str) -> str:
    opts = YTDL_OPTS.copy()
    opts["outtmpl"] = os.path.join(dest_dir, opts["outtmpl"])
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


# --- Telegram отправка ---
async def send_file(update: Update, filepath: str, caption: str = ""):
    filesize = os.path.getsize(filepath)
    field_name = "video" if filesize <= MAX_VIDEO_SIZE else "document"
    with open(filepath, "rb") as f:
        if field_name == "video":
            await update.message.reply_video(video=f, caption=caption)
        else:
            await update.message.reply_document(document=f, caption=caption)


# --- Обработка URL ---
async def handle_reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    await update.message.reply_text("Скачиваю Reel, подождите...")
    tmpdir = tempfile.mkdtemp(prefix="reel_")
    try:
        # Чтобы не блокировать event loop, скачиваем в отдельном потоке
        filepath = await asyncio.to_thread(download_reel, url, tmpdir)
        await send_file(update, filepath)
    except Exception as e:
        logger.exception("Ошибка при скачивании")
        await update.message.reply_text(f"Ошибка: {e}")
    finally:
        shutil.rmtree(tmpdir)


# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Пришли ссылку на Instagram Reel, я скачаю и пришлю тебе видео."
    )


# --- Основной запуск ---
def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Нужно установить TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reel))

    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
