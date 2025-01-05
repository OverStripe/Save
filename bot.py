# File: bot.py

import os
import logging
import re
import asyncio
from datetime import datetime, time
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackContext,
)
from instaloader import Instaloader, Post
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL")
DEV_USERNAME = os.getenv("DEV_USERNAME")
DEV_USER_ID = int(os.getenv("DEV_USER_ID"))
REMINDER_TIME = os.getenv("REMINDER_TIME", "09:00")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Instaloader
loader = Instaloader()

# URL validation regex
INSTAGRAM_URL_PATTERN = re.compile(
    r"(https?://(?:www\.)?instagram\.com/(p|reel|tv)/[\w\-]+/?(?:\?igsh=[\w\-]+)?)"
)

# Bot Stats
bot_start_time = datetime.now()
download_stats = {
    "total_downloads": 0,
    "user_downloads": {}
}

# Track users for reminders
user_list = set()


# ------------------------
# ❖ Start Command
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a welcome message with inline buttons and instructions.
    """
    user = update.effective_user
    full_name = f"{user.first_name or 'User'} {user.last_name or ''}".strip()
    user_list.add(user.id)

    keyboard = [
        [InlineKeyboardButton("❖ 💻 Developer", url=f"https://t.me/{DEV_USERNAME}")],
    ]

    if SUPPORT_CHANNEL:
        keyboard.append([InlineKeyboardButton("❖ 📢 Support Channel", url=SUPPORT_CHANNEL)])

    keyboard.append([InlineKeyboardButton("❖ ℹ️ Help", callback_data='help')])
    keyboard.append([InlineKeyboardButton("❖ 📥 Example Download", callback_data='example')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"**❖ 👋 Welcome, {full_name}! 🌟**\n\n"
        "**❖ What Can I Do?**\n"
        "- ❖ 📸 **/Download <URL>** → Download Instagram Media\n"
        "- ❖ 📊 **/Stats** → Admin Only Bot Stats\n\n"
        "**❖ How To Use:**\n"
        "1️⃣ Copy The Instagram Post URL.\n"
        "2️⃣ Send `/Download <URL>` To This Bot.\n"
        "3️⃣ Enjoy Your Media! 🥳\n\n"
        "**❖ Quick Access Below:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ------------------------
# ❖ Download Command with Animated Emojis
# ------------------------
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Download Instagram media with animated emoji-based progress updates.
    """
    user = update.effective_user
    user_list.add(user.id)

    if len(context.args) == 0:
        await update.message.reply_text("❖ ⚠️ **Please Provide A Valid Instagram URL.**")
        return

    url = context.args[0]
    if not INSTAGRAM_URL_PATTERN.match(url):
        await update.message.reply_text(
            "❖ ⚠️ **Invalid Instagram URL.**\n"
            "Ensure it starts with `https://` and matches formats like:\n"
            "- `https://www.instagram.com/p/ID/`\n"
            "- `https://www.instagram.com/reel/ID/`\n"
            "- `https://www.instagram.com/tv/ID/`"
        )
        return

    sent_message = await update.message.reply_text("❖ ⏳ **Preparing Your Download... 🛠️**")
    
    stages = [
        "❖ ⏳ **Downloading Media... 📥**",
        "❖ 🔄 **Extracting Content... 🔧**",
        "❖ 💾 **Saving Media... 💻**",
        "❖ ✅ **Download Complete! 🎉**"
    ]

    for stage in stages:
        await asyncio.sleep(1.5)
        await sent_message.edit_text(stage)
    
    try:
        shortcode = re.search(r"/(p|reel|tv)/([\w\-]+)", url).group(2)
        post = Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=user.username or "instagram_download")

        await sent_message.edit_text("❖ ✅ **Media Downloaded Successfully! 🎯**")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await sent_message.edit_text(
            f"❖ ❌ **Failed To Download Media. 😔**\nError: {str(e)}"
        )


# ------------------------
# ❖ Stats Command (Admin Only)
# ------------------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Display bot stats (Admin Only).
    """
    user = update.effective_user
    if user.id != DEV_USER_ID:
        await update.message.reply_text("❖ ⚠️ **This Command Is Admin Only. 🚫**")
        return

    uptime = datetime.now() - bot_start_time
    await update.message.reply_text(
        f"❖ 📊 **Bot Stats:**\n\n"
        f"❖ 🕒 **Uptime:** {uptime}\n"
        f"❖ 📥 **Total Downloads:** {download_stats['total_downloads']} 📊\n"
        f"❖ 👤 **Unique Users:** {len(download_stats['user_downloads'])} 👥"
    )


# ------------------------
# ❖ Daily Reminder Job
# ------------------------
async def daily_reminder(context: CallbackContext) -> None:
    for user_id in user_list:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❖ ⚠️ **Don't Miss Important Updates!**\n📢 [Join @TechPiroBots]({SUPPORT_CHANNEL})",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send reminder to {user_id}: {e}")


# ------------------------
# ❖ Main Function
# ------------------------
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue = application.job_queue
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CommandHandler("stats", stats))

    reminder_hour, reminder_minute = map(int, REMINDER_TIME.split(':'))
    job_queue.run_daily(daily_reminder, time=time(reminder_hour, reminder_minute))
    
    application.run_polling()


if __name__ == '__main__':
    main()
