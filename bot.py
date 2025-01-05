# File: bot.py

import os
import logging
import httpx
import asyncio
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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL")
DEV_USERNAME = os.getenv("DEV_USERNAME")
DEV_USER_ID = int(os.getenv("DEV_USER_ID"))
API_URL = os.getenv("API_URL")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ------------------------
# ❖ Start Command
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a welcome message with instructions and buttons.
    """
    user = update.effective_user
    full_name = f"{user.first_name or 'User'} {user.last_name or ''}".strip()

    keyboard = [
        [InlineKeyboardButton("❖ 💻 Developer", url=f"https://t.me/{DEV_USERNAME}")],
    ]

    if SUPPORT_CHANNEL:
        keyboard.append([InlineKeyboardButton("❖ 📢 Support Channel", url=SUPPORT_CHANNEL)])

    keyboard.append([InlineKeyboardButton("❖ ℹ️ Help", callback_data='help')])
    keyboard.append([InlineKeyboardButton("❖ 📥 Example Download", callback_data='example')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "❖ 👋 **Welcome!** 🌟\n\n"
        "❖ **What Can I Do?**\n"
        "❖ 📸 **/ig <URL>** → Download Instagram Media (Photo & Video)\n"
        "❖ 📊 **/stats** → Admin Only Bot Stats\n\n"
        "❖ **How To Use:**\n"
        "❖ 🔗 Copy The Instagram Post URL.\n"
        "❖ 📤 Send `/ig <URL>` To This Bot.\n"
        "❖ 🎥 Enjoy Your Media!\n\n"
        "❖ **Quick Access Below:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ------------------------
# ❖ Instagram Download Command (/ig) with Emoji Animations and Video Support
# ------------------------
async def ig_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Download Instagram media using an API and send it to the user with emoji animations.
    """
    if len(context.args) == 0:
        await update.message.reply_text("❖ ⚠️ **Please Provide A Valid Instagram URL.**")
        return

    url = context.args[0]
    sent_message = await update.message.reply_text("❖ ⏳ **Fetching Media... Please Wait!**")

    try:
        # Emoji animation stages
        stages = [
            "❖ ⏳ **Validating URL...** 🔗",
            "❖ 🔄 **Connecting To Server...** 🌐",
            "❖ 📥 **Downloading Media...** 📸",
            "❖ 💾 **Processing File...** 🛠️",
            "❖ ✅ **Almost Done...** 🎯"
        ]

        # Simulate animation stages
        for stage in stages:
            await asyncio.sleep(1.5)
            await sent_message.edit_text(stage)

        # Fetch media from API
        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL, params={"url": url})
            response.raise_for_status()
            data = response.json()

        content_url = data.get("content_url")
        if content_url:
            if content_url.endswith(('.jpg', '.jpeg', '.png')):
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=content_url,
                    caption="❖ ✅ **Here is your Instagram Photo!** 📸"
                )
            elif content_url.endswith('.mp4'):
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=content_url,
                    caption="❖ ✅ **Here is your Instagram Video!** 🎥"
                )
            else:
                await sent_message.edit_text("❖ ⚠️ **Unsupported Content Type Found.**")
            
            await sent_message.edit_text("❖ ✅ **Media Sent Successfully! 🎉**")
        else:
            await sent_message.edit_text("❖ ⚠️ **Unable To Fetch Content. Please Check The URL.**")

    except httpx.HTTPStatusError as e:
        logger.error(f"❖ ❌ API Error: {e}")
        await sent_message.edit_text("❖ ❌ **API Error. Please Try Again Later.**")
    except Exception as e:
        logger.error(f"❖ ❌ Error: {e}")
        await sent_message.edit_text(f"❖ ❌ **An Error Occurred:** {str(e)}")


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

    await update.message.reply_text(
        f"❖ 📊 **Bot Stats:**\n\n"
        f"❖ 🕒 **Uptime:** Active\n"
        f"❖ 📥 **Total Downloads:** API Based\n"
        f"❖ 👤 **Unique Users:** API Based"
    )


# ------------------------
# ❖ Error Handler
# ------------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"❖ ❌ Update {update} caused error {context.error}")


# ------------------------
# ❖ Main Function
# ------------------------
def main():
    """
    Start the Telegram bot application.
    """
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ig", ig_command_handler))
    application.add_handler(CommandHandler("stats", stats))

    # Error Handler
    application.add_error_handler(error_handler)

    # Start the Bot
    logger.info("❖ 🚀 Bot is starting...")
    application.run_polling()


if __name__ == '__main__':
    main()
