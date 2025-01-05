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
# ✅ Check Command (Three Options)
# ------------------------

# ✅ Option 1: Forwarded Message Validation
async def check_option1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "**🔍 Subscription Check Required**\n\n"
        "Please Forward Any Message From Our Channel To This Bot:\n"
        f"📢 [{SUPPORT_CHANNEL}]({SUPPORT_CHANNEL})",
        parse_mode='Markdown'
    )


# ✅ Option 2: Inline Button Validation
async def check_option2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("📢 Verify Subscription", url=SUPPORT_CHANNEL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "**🔍 Subscription Check Required**\n\n"
        "Please Click The Button Below To Verify Your Subscription:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ✅ Option 3: Manual Confirmation (Developer Only)
async def check_option3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id != DEV_USER_ID:
        await update.message.reply_text("⚠️ **This Option Is Only Available For The Developer.**")
        return
    
    keyboard = [
        [InlineKeyboardButton("📢 Join Our Channel", url=SUPPORT_CHANNEL)],
        [InlineKeyboardButton("✅ I Have Joined", callback_data='confirm_subscription')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "**🔍 Manual Subscription Check (Admin Only)**\n\n"
        "1️⃣ Click 'Join Our Channel'.\n"
        "2️⃣ After Joining, Click '✅ I Have Joined'.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ✅ Callback Handler for Manual Confirmation
async def confirm_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user

    if await is_user_subscribed(context, user.id):
        await query.answer("✅ You Are Subscribed!")
        await query.edit_message_text("✅ **You Are Subscribed To The Channel!**")
    else:
        await query.answer("❌ Subscription Not Detected.")
        await query.edit_message_text(
            "⚠️ **It Seems You Are Not Subscribed.**\n\n"
            "Please Join The Channel And Try Again."
        )


# ------------------------
# 🚀 Main Function
# ------------------------
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CommandHandler("check_option1", check_option1))
    application.add_handler(CommandHandler("check_option2", check_option2))
    application.add_handler(CommandHandler("check_option3", check_option3))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(confirm_subscription, pattern='^confirm_subscription$'))
    application.run_polling()


if __name__ == '__main__':
    main()
