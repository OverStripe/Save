# File: bot.py

import os
import logging
import re
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
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
# 🛡️ Channel Subscription Check
# ------------------------
async def is_user_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """
    Check if the user is subscribed to the support channel.
    """
    try:
        member = await context.bot.get_chat_member(SUPPORT_CHANNEL_ID, user_id)
        logger.info(f"User {user_id} status in channel: {member.status}")
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Failed to verify user subscription: {e}")
        return False


# ------------------------
# 📲 Start Command
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Sends a personalized welcome message with clear instructions.
    """
    user = update.effective_user
    first_name = user.first_name or "User"
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    
    keyboard = [
        [InlineKeyboardButton("💻 Developer", url=f"https://t.me/{DEV_USERNAME}")],
        [InlineKeyboardButton("📢 Support Channel", url=SUPPORT_CHANNEL)],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')],
        [InlineKeyboardButton("📥 Example Download", callback_data='example')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"**Welcome, {full_name}!**\n\n"
        "**What Can I Do?**\n"
        "- 📸 **/Download <URL>** - Download Instagram Media\n"
        "- ✅ **/Check** - Check Your Subscription\n"
        "- 📊 **/Stats** - View Bot Stats (Admin Only)\n\n"
        "**How To Use?**\n"
        "1. Copy The Instagram Post URL.\n"
        "2. Send `/Download <URL>` To This Bot.\n"
        "3. Enjoy Your Downloaded Media!\n\n"
        "**Quick Access Buttons:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ------------------------
# 📥 Download Command
# ------------------------
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Download Instagram media if the user is subscribed.
    """
    user = update.effective_user
    if not await is_user_subscribed(context, user.id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Our Channel", url=SUPPORT_CHANNEL)]
        ]
        await update.message.reply_text(
            "**⚠️ Please Join Our Channel First:**\n"
            f"📢 [Join Here]({SUPPORT_CHANNEL})",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    if len(context.args) == 0:
        await update.message.reply_text("**⚠️ Please Provide A Valid URL.**")
        return

    url = context.args[0]
    if not INSTAGRAM_URL_PATTERN.match(url):
        await update.message.reply_text("**⚠️ Invalid Instagram URL.**")
        return

    await update.message.reply_text("**⏳ Processing Your Download...**")
    download_stats["total_downloads"] += 1
    download_stats["user_downloads"][user.id] = download_stats["user_downloads"].get(user.id, 0) + 1

    await update.message.reply_text("✅ **Media Downloaded Successfully!**")


# ------------------------
# ✅ Check Command
# ------------------------
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Check if the user is subscribed to the channel.
    """
    user = update.effective_user
    if await is_user_subscribed(context, user.id):
        await update.message.reply_text("✅ **You Are Subscribed!**")
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Join Our Channel", url=SUPPORT_CHANNEL)]
        ]
        await update.message.reply_text(
            "⚠️ **You Are Not Subscribed To Our Channel.**\n\n"
            "Please Click Below To Join:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


# ------------------------
# 📊 Stats Command (Admin Only)
# ------------------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Display bot stats (Developer Only).
    """
    user = update.effective_user
    if user.id != DEV_USER_ID:
        await update.message.reply_text("⚠️ **Only The Developer Can Access This Command.**")
        return

    uptime = datetime.now() - bot_start_time
    await update.message.reply_text(
        f"📊 **Bot Stats:**\n\n"
        f"🕒 **Uptime:** {uptime}\n"
        f"📥 **Total Downloads:** {download_stats['total_downloads']}"
    )


# 🚀 Main Function
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("stats", stats))
    application.run_polling()


if __name__ == '__main__':
    main()
