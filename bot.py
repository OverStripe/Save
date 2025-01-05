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

# ✜ Load Environment Variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL")
DEV_USERNAME = os.getenv("DEV_USERNAME")
DEV_USER_ID = int(os.getenv("DEV_USER_ID"))
API_URL = os.getenv("API_URL")

# ✜ Logging Configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# ✜ Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a personalized welcome message with command list and buttons.
    """
    user = update.effective_user
    full_name = f"{user.first_name or 'User'} {user.last_name or ''}".strip()

    keyboard = [
        [InlineKeyboardButton("✜ Developer", url=f"https://t.me/{DEV_USERNAME}")],
    ]

    if SUPPORT_CHANNEL:
        keyboard.append([InlineKeyboardButton("✜ Support", url=SUPPORT_CHANNEL)])

    keyboard.append([InlineKeyboardButton("✜ Help", callback_data='help')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✜ Welcome, {full_name}!\n\n"
        "✜ Use `/ig <URL>` to download Instagram media.\n"
        "✜ Admins can use `/stats`.\n"
        "✜ Get help using `/help`.\n\n"
        "✜ Quick Links Below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


# ✜ Help Command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Display all available commands.
    """
    await update.message.reply_text(
        "✜ Available Commands:\n\n"
        "✜ `/start` → Start the bot\n"
        "✜ `/ig <URL>` → Download Instagram Media\n"
        "✜ `/stats` → Admin Stats (Developer Only)\n"
        "✜ `/help` → Show all commands\n\n"
        "✜ Example Usage:\n"
        "`/ig https://www.instagram.com/reel/EXAMPLE/`\n\n"
        "✜ For Support:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✜ Support", url=SUPPORT_CHANNEL)],
            [InlineKeyboardButton("✜ Developer", url=f"https://t.me/{DEV_USERNAME}")]
        ]),
        parse_mode='HTML'
    )


# ✜ Instagram Download Command
async def ig_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Download Instagram media via API and send it to the user.
    """
    if len(context.args) == 0:
        await update.message.reply_text("✜ Please provide a valid Instagram URL.")
        return

    url = context.args[0]
    logger.debug(f"✜ Received URL: {url}")
    sent_message = await update.message.reply_text("✜ Fetching Media... Please Wait!")

    try:
        # ✜ Animated Progress
        stages = [
            "✜ Validating URL...",
            "✜ Connecting to Server...",
            "✜ Fetching Media...",
            "✜ Processing Media...",
            "✜ Finalizing..."
        ]

        for stage in stages:
            await asyncio.sleep(1.5)
            await sent_message.edit_text(stage)

        # ✜ Fetch Media via API
        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL, params={"url": url})
            response.raise_for_status()
            data = response.json()

        logger.debug(f"✜ API Response: {data}")
        content_url = data.get("content_url")

        if content_url:
            try:
                if content_url.endswith(('.jpg', '.jpeg', '.png')):
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=content_url,
                        caption="✜ Here is your Instagram Photo!"
                    )
                elif content_url.endswith('.mp4') or '/videos/' in content_url:
                    async with httpx.AsyncClient() as client:
                        video_response = await client.head(content_url)
                        content_length = int(video_response.headers.get('Content-Length', 0))
                        max_size = 50 * 1024 * 1024  # 50MB limit

                        if content_length > max_size:
                            raise ValueError("Video size exceeds Telegram limits.")
                        await context.bot.send_video(
                            chat_id=update.effective_chat.id,
                            video=content_url,
                            caption="✜ Here is your Instagram Video!"
                        )
                else:
                    raise ValueError("Unsupported content type.")
            except Exception:
                await update.message.reply_text(
                    f"✜ Unable to send media directly.\n"
                    f"✜ Download it here: [Direct Link]({content_url})",
                    disable_web_page_preview=True
                )
        else:
            await sent_message.edit_text("✜ No media found. Please check the URL.")

    except httpx.HTTPStatusError as e:
        logger.error(f"✜ API Error: {e}")
        await update.message.reply_text("✜ API Error. Please try again later.")
    except Exception as e:
        logger.error(f"✜ Error: {e}")
        await update.message.reply_text(
            f"✜ An error occurred. You can download manually here:\n"
            f"[Direct Link]({url})",
            disable_web_page_preview=True
        )


# ✜ Stats Command (Admin Only)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Display bot stats (Developer Only).
    """
    user = update.effective_user
    if user.id != DEV_USER_ID:
        await update.message.reply_text("✜ This command is restricted to the developer.")
        return

    await update.message.reply_text(
        "✜ Bot Stats:\n"
        "✜ Uptime: Active\n"
        "✜ Total Downloads: API Based"
    )


# ✜ Main Function
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ig", ig_command_handler))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))
    logger.info("✜ Bot is starting...")
    application.run_polling()


if __name__ == '__main__':
    main()
