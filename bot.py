# File: bot.py

import os
import logging
import re
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)
from instaloader import Instaloader, Post
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL")
DEV_USERNAME = os.getenv("DEV_USERNAME")
SUPPORT_CHANNEL_ID = int(os.getenv("SUPPORT_CHANNEL_ID"))
DEV_USER_ID = int(os.getenv("DEV_USER_ID"))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Instaloader
loader = Instaloader()

# URL validation regex
INSTAGRAM_URL_PATTERN = re.compile(r"(https?://(www\.)?instagram\.com/p/[\w-]+/)")

# Bot Stats
bot_start_time = datetime.now()
download_stats = {
    "total_downloads": 0,
    "user_downloads": {}
}

# ------------------------
# 🛡️ CHANNEL SUBSCRIPTION CHECK
# ------------------------
async def is_user_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(SUPPORT_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking channel subscription: {e}")
        return False

async def enforce_channel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not await is_user_subscribed(context, user.id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Our Channel", url=SUPPORT_CHANNEL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ **You must subscribe to our channel before using this bot.**\n\n"
            f"📢 [Join Channel]({SUPPORT_CHANNEL})",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return False
    return True

# ------------------------
# 📲 START COMMAND
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await enforce_channel_subscription(update, context):
        return
    
    keyboard = [
        [InlineKeyboardButton("💻 Developer", url=f"https://t.me/{DEV_USERNAME}")],
        [InlineKeyboardButton("📢 Channel", url=SUPPORT_CHANNEL)],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')],
        [InlineKeyboardButton("📥 Download Example", callback_data='example')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "━❖ **Philo ❖ Downloader ❖** ━\n\n"
        "👋 **Welcome to the Philo Downloader Bot!**\n\n"
        "🔗 **How to Use:**\n"
        "1️⃣ Send me an Instagram post URL.\n"
        "2️⃣ Use `/download <URL>` to fetch media.\n\n"
        "📲 **Quick Access Below:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ------------------------
# 📥 DOWNLOAD COMMAND
# ------------------------
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await enforce_channel_subscription(update, context):
        return

    user = update.effective_user
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Please provide an Instagram post URL.\nUsage: `/download <URL>`")
        return

    url = context.args[0]
    if not INSTAGRAM_URL_PATTERN.match(url):
        await update.message.reply_text("⚠️ Invalid Instagram URL. Please provide a valid Instagram post URL.")
        return

    await update.message.reply_text("⏳ **Downloading your media... Please wait.**")
    try:
        shortcode = url.split("/p/")[1].split("/")[0]
        post = Post.from_shortcode(loader.context, shortcode)

        loader.download_post(post, target='downloads')
        file_path = f"downloads/{shortcode}.{'mp4' if post.is_video else 'jpg'}"
        
        if post.is_video:
            await update.message.reply_video(open(file_path, "rb"))
        else:
            await update.message.reply_photo(open(file_path, "rb"))

        download_stats["total_downloads"] += 1
        download_stats["user_downloads"][user.id] = download_stats["user_downloads"].get(user.id, 0) + 1

        await update.message.reply_text("✅ **Download Complete! Enjoy your media.**")

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Failed to download the post. Please try again later.")

# ------------------------
# ℹ️ HELP COMMAND
# ------------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🏠 Home", callback_data='home')],
        [InlineKeyboardButton("📢 Channel", url=SUPPORT_CHANNEL)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "**ℹ️ Help Menu**\n\n"
        "📝 **Commands:**\n"
        "- `/start` → Start the bot.\n"
        "- `/download <URL>` → Download Instagram media.\n"
        "- `/stats` → (Developer Only)\n\n"
        "📲 Use the buttons below for quick access.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ------------------------
# 🚀 MAIN FUNCTION
# ------------------------
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", download))
    application.run_polling()

if __name__ == '__main__':
    main()
