# File: bot.py

import os
import logging
import re
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from instaloader import Instaloader
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
# 🛡️ Subscription Check
# ------------------------
async def is_user_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """
    Verify if the user is subscribed to the support channel.
    """
    try:
        member = await context.bot.get_chat_member(SUPPORT_CHANNEL_ID, user_id)
        logger.info(f"User {user_id} membership status: {member.status}")
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Failed to verify subscription: {e}")
        return False


# ------------------------
# 📲 Start Command
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Welcome the user with inline buttons and instructions.
    """
    user = update.effective_user
    full_name = f"{user.first_name or 'User'} {user.last_name or ''}".strip()

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
        "- 📸 **/Download <URL>** → Download Instagram Media\n"
        "- ✅ **/Check** → Check Your Subscription\n"
        "- 📊 **/Stats** → Admin Only Bot Stats\n\n"
        "**How To Use:**\n"
        "1️⃣ Copy The Instagram Post URL.\n"
        "2️⃣ Send `/Download <URL>` To This Bot.\n"
        "3️⃣ Enjoy Your Media!\n\n"
        "**Quick Access Buttons Below:**",
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
        keyboard = [[InlineKeyboardButton("📢 Join Our Channel", url=SUPPORT_CHANNEL)]]
        await update.message.reply_text(
            "**⚠️ Please Join Our Channel First:**\n"
            f"📢 [Join Here]({SUPPORT_CHANNEL})",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    if len(context.args) == 0:
        await update.message.reply_text("⚠️ **Please Provide A Valid URL.**")
        return

    url = context.args[0]
    if not INSTAGRAM_URL_PATTERN.match(url):
        await update.message.reply_text("⚠️ **Invalid Instagram URL.**")
        return

    await update.message.reply_text("⏳ **Processing Your Download...**")
    download_stats["total_downloads"] += 1
    download_stats["user_downloads"][user.id] = download_stats["user_downloads"].get(user.id, 0) + 1

    await update.message.reply_text("✅ **Media Downloaded Successfully!**")


# ------------------------
# ✅ Check Options
# ------------------------

# Option 1: Forwarded Message Validation
async def check_option1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "**🔍 Subscription Check Required**\n"
        "Please Forward Any Message From Our Channel To This Bot:\n"
        f"📢 [{SUPPORT_CHANNEL}]({SUPPORT_CHANNEL})",
        parse_mode='Markdown'
    )

# Option 2: Inline Button Validation
async def check_option2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("📢 Verify Subscription", url=SUPPORT_CHANNEL)]]
    await update.message.reply_text(
        "**🔍 Click The Button Below To Verify Subscription:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# Option 3: Manual Confirmation (Admin Only)
async def check_option3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != DEV_USER_ID:
        await update.message.reply_text("⚠️ **This Option Is Developer Only.**")
        return

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=SUPPORT_CHANNEL)],
        [InlineKeyboardButton("✅ I Have Joined", callback_data='confirm_subscription')]
    ]
    await update.message.reply_text(
        "**🔍 Admin Subscription Check**\n"
        "1️⃣ Join Our Channel\n"
        "2️⃣ Click '✅ I Have Joined'",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# 🚀 Main Function
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CommandHandler("check_option1", check_option1))
    application.add_handler(CommandHandler("check_option2", check_option2))
    application.add_handler(CommandHandler("check_option3", check_option3))
    application.run_polling()


if __name__ == '__main__':
    main()
    
