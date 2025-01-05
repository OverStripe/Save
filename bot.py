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
# ⚡ Start Command
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a welcome message with instructions and buttons.
    """
    user = update.effective_user
    full_name = f"{user.first_name or 'User'} {user.last_name or ''}".strip()

    keyboard = [
        [InlineKeyboardButton("⚡ 💻 Developer", url=f"https://t.me/{DEV_USERNAME}")],
    ]

    if SUPPORT_CHANNEL:
        keyboard.append([InlineKeyboardButton("⚡ 📢 Support Channel", url=SUPPORT_CHANNEL)])

    keyboard.append([InlineKeyboardButton("⚡ ℹ️ Help", callback_data='help')])
    keyboard.append([InlineKeyboardButton("⚡ 📥 Example Download", callback_data='example')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚡✨ **Welcome to the Ultimate Instagram Downloader Bot!** ✨⚡\n\n"
        "⚡ **Available Commands:**\n"
        "⚡ `/ig <URL>` → Download Instagram Media\n"
        "⚡ `/stats` → Admin Only Stats\n\n"
        "⚡ **Quick Start Guide:**\n"
        "⚡ 🔗 Copy an Instagram media URL.\n"
        "⚡ 📤 Send it using `/ig <URL>`.\n"
        "⚡ 🎥 Enjoy seamless downloads!\n\n"
        "⚡ **Quick Access Below:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ------------------------
# ⚡ Instagram Download Command (/ig) with Full Content Support
# ------------------------
async def ig_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Download Instagram media using an API and send it to the user.
    Supports all content types: Photos, Videos, Carousels.
    """
    if len(context.args) == 0:
        await update.message.reply_text("⚡⚠️ **Please Provide A Valid Instagram URL.**")
        return

    url = context.args[0]
    sent_message = await update.message.reply_text("⚡🌀 **Initializing Media Fetch... Please Wait!**")

    try:
        # Animated Progress Stages
        stages = [
            "⚡🔗 **Validating URL...**",
            "⚡🌐 **Connecting to Instagram Servers...**",
            "⚡📥 **Fetching Media Details...**",
            "⚡🛠️ **Processing Content...**",
            "⚡🎯 **Finalizing Your Request...**"
        ]

        for stage in stages:
            await asyncio.sleep(1.5)
            await sent_message.edit_text(stage)

        # Fetch media from API
        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL, params={"url": url})
            response.raise_for_status()
            data = response.json()

        contents = data.get("content_urls", [data.get("content_url")])
        
        if not contents:
            await sent_message.edit_text("⚡❌ **No Media Found. Please Check The URL.**")
            return

        # Handle multiple content items (Carousel or Single Content)
        for idx, content_url in enumerate(contents):
            if content_url.endswith(('.jpg', '.jpeg', '.png')):
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=content_url,
                    caption=f"⚡✅ **Photo {idx + 1} Sent Successfully!**"
                )
            elif content_url.endswith('.mp4') or '/videos/' in content_url:
                # Check if video size is within Telegram limits
                async with httpx.AsyncClient() as client:
                    video_response = await client.head(content_url)
                    content_length = int(video_response.headers.get('Content-Length', 0))
                    max_size = 50 * 1024 * 1024  # 50MB limit for Telegram bots

                    if content_length > max_size:
                        await update.message.reply_text(
                            f"⚡🚫 **Video {idx + 1} is too large to send on Telegram.**\n"
                            f"⚡🔗 **Direct Link:** [Click Here]({content_url})",
                            disable_web_page_preview=True
                        )
                    else:
                        await context.bot.send_video(
                            chat_id=update.effective_chat.id,
                            video=content_url,
                            caption=f"⚡✅ **Video {idx + 1} Sent Successfully!**"
                        )
            else:
                await sent_message.edit_text("⚡❌ **Unsupported Content Type Found.**")

        await sent_message.edit_text("⚡🎉 **All Media Sent Successfully!**")

    except httpx.HTTPStatusError as e:
        logger.error(f"⚡❌ API Error: {e}")
        await sent_message.edit_text("⚡❌ **API Error. Please Try Again Later.**")
    except Exception as e:
        logger.error(f"⚡❌ Error: {e}")
        await sent_message.edit_text(f"⚡❌ **An Error Occurred:** {str(e)}")


# ------------------------
# ⚡ Stats Command (Admin Only)
# ------------------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Display bot stats (Admin Only).
    """
    user = update.effective_user
    if user.id != DEV_USER_ID:
        await update.message.reply_text("⚡🚫 **This Command Is Admin Only.**")
        return

    await update.message.reply_text(
        f"⚡📊 **Bot Stats:**\n\n"
        f"⚡🕒 **Uptime:** Active\n"
        f"⚡📥 **Total Downloads:** API Based\n"
        f"⚡👤 **Unique Users:** API Based"
    )


# ------------------------
# ⚡ Main Function
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

    # Start the Bot
    logger.info("⚡ Bot is starting...")
    application.run_polling()


if __name__ == '__main__':
    main()
