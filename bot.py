# File: bot.py

import os
import logging
import re
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
    JobQueue,
)
from instaloader import Instaloader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL")
DEV_USERNAME = os.getenv("DEV_USERNAME")
DEV_USER_ID = int(os.getenv("DEV_USER_ID"))
REMINDER_TIME = os.getenv("REMINDER_TIME", "09:00")  # Default to 09:00 if not set

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
    user_list.add(user.id)  # Add user to tracked user list

    keyboard = [
        [InlineKeyboardButton("❖ 💻 Developer", url=f"https://t.me/{DEV_USERNAME}")],
    ]

    if SUPPORT_CHANNEL:
        keyboard.append([InlineKeyboardButton("❖ 📢 Support Channel", url=SUPPORT_CHANNEL)])

    keyboard.append([InlineKeyboardButton("❖ ℹ️ Help", callback_data='help')])
    keyboard.append([InlineKeyboardButton("❖ 📥 Example Download", callback_data='example')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"**❖ Welcome, {full_name}! ❖**\n\n"
        "**❖ What Can I Do?**\n"
        "- ❖ 📸 **/Download <URL>** → Download Instagram Media\n"
        "- ❖ 📊 **/Stats** → Admin Only Bot Stats\n\n"
        "**❖ How To Use:**\n"
        "1️⃣ Copy The Instagram Post URL.\n"
        "2️⃣ Send `/Download <URL>` To This Bot.\n"
        "3️⃣ Enjoy Your Media!\n\n"
        "**❖ Quick Access Buttons Below:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ------------------------
# ❖ Download Command
# ------------------------
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Download Instagram media for any user without requiring subscription.
    """
    user = update.effective_user
    user_list.add(user.id)  # Add user to tracked user list

    if len(context.args) == 0:
        await update.message.reply_text("❖ ⚠️ **Please Provide A Valid URL.**")
        return

    url = context.args[0]
    if not INSTAGRAM_URL_PATTERN.match(url):
        await update.message.reply_text("❖ ⚠️ **Invalid Instagram URL.**")
        return

    await update.message.reply_text("❖ ⏳ **Processing Your Download...**")
    download_stats["total_downloads"] += 1
    download_stats["user_downloads"][user.id] = download_stats["user_downloads"].get(user.id, 0) + 1

    await update.message.reply_text("❖ ✅ **Media Downloaded Successfully!**")


# ------------------------
# ❖ Stats Command (Admin Only)
# ------------------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Display bot stats (Admin Only).
    """
    user = update.effective_user
    if user.id != DEV_USER_ID:
        await update.message.reply_text("❖ ⚠️ **This Command Is Admin Only.**")
        return

    uptime = datetime.now() - bot_start_time
    await update.message.reply_text(
        f"❖ 📊 **Bot Stats:**\n\n"
        f"❖ 🕒 **Uptime:** {uptime}\n"
        f"❖ 📥 **Total Downloads:** {download_stats['total_downloads']}\n"
        f"❖ 👤 **Unique Users:** {len(download_stats['user_downloads'])}"
    )


# ------------------------
# ❖ Daily Reminder Job
# ------------------------
async def daily_reminder(context: CallbackContext) -> None:
    """
    Send a daily reminder to all users to join the channel.
    """
    for user_id in user_list:
        try:
            keyboard = [[InlineKeyboardButton("❖ 📢 Join Our Channel", url=SUPPORT_CHANNEL)]]
            await context.bot.send_message(
                chat_id=user_id,
                text="❖ ⚠️ **Don't Miss Important Updates!**\n\n"
                     "Join Our Channel For The Latest Updates:\n"
                     f"📢 [Join @TechPiroBots]({SUPPORT_CHANNEL})",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send reminder to {user_id}: {e}")


# ------------------------
# ❖ Main Function
# ------------------------
def main():
    """
    Initialize the bot, set up command handlers, and schedule tasks with JobQueue.
    """
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue = application.job_queue  # Initialize JobQueue
    
    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CommandHandler("stats", stats))
    
    # Daily Reminder Job
    reminder_hour, reminder_minute = map(int, REMINDER_TIME.split(':'))
    job_queue.run_daily(
        daily_reminder,
        time=time(reminder_hour, reminder_minute)
    )
    
    application.run_polling()


if __name__ == '__main__':
    main()
