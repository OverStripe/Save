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
# 🛡️ CHANNEL SUBSCRIPTION CHECK
# ------------------------
async def is_user_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(SUPPORT_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking channel subscription: {e}")
        return False

# ------------------------
# 📲 START COMMAND
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ", url=f"https://t.me/{DEV_USERNAME}")],
        [InlineKeyboardButton("📢 ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=SUPPORT_CHANNEL)],
        [InlineKeyboardButton("ℹ️ ʜᴇʟᴘ", callback_data='help')],
        [InlineKeyboardButton("📥 ᴇxᴀᴍᴘʟᴇ ᴅᴏᴡɴʟᴏᴀᴅ", callback_data='example')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "**━❖ ᴾᴴᴵᴸᴼ ❖ ᴰᴼᵂᴺᴸᴼᴬᴰᴱᴿ ❖━**\n\n"
        "👋 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴘʜɪʟᴏ ᴅᴏᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ!**\n\n"
        "✨ **ᴡʜᴀᴛ ɪ ᴄᴀɴ ᴅᴏ:**\n"
        "- 🔹 **/Download <URL> → ᴅᴏᴡɴʟᴏᴀᴅ ɪɴꜱᴛᴀɢʀᴀᴍ ᴍᴇᴅɪᴀ.**\n"
        "- 🔹 **/Check → ᴄʜᴇᴄᴋ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.**\n"
        "- 🔹 **/Help → ᴠɪᴇᴡ ʜᴇʟᴘ ᴍᴇɴᴜ.**\n\n"
        "📲 **ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ꜱᴛᴀʀᴛ!**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ------------------------
# 📥 DOWNLOAD COMMAND
# ------------------------
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_subscribed(context, user.id):
        await update.message.reply_text(
            "⚠️ **ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ:**\n"
            f"📢 [ᴊᴏɪɴ ʜᴇʀᴇ]({SUPPORT_CHANNEL})",
            parse_mode='Markdown'
        )
        return

    if len(context.args) == 0:
        await update.message.reply_text("⚠️ **ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴜʀʟ.**")
        return

    url = context.args[0]
    if not INSTAGRAM_URL_PATTERN.match(url):
        await update.message.reply_text("⚠️ **ɪɴᴠᴀʟɪᴅ ᴜʀʟ.**")
        return

    await update.message.reply_text("⏳ **ᴘʀᴏᴄᴇꜱꜱɪɴɢ ᴅᴏᴡɴʟᴏᴀᴅ...**")

# ------------------------
# ✅ CHECK COMMAND
# ------------------------
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if await is_user_subscribed(context, user.id):
        await update.message.reply_text("✅ **ʏᴏᴜ'ʀᴇ ꜱᴜʙꜱᴄʀɪʙᴇᴅ!**")
    else:
        await update.message.reply_text("⚠️ **ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ.**")

# ------------------------
# 🚀 MAIN FUNCTION
# ------------------------
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CommandHandler("check", check))
    application.run_polling()

if __name__ == '__main__':
    main()
