# File: instagram_bot.py

import os
import logging
import re
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
BOT_TOKEN = os.getenv("7586801948:AAGK1zlwSC6E-zOuUqJNtyaqAoMOWg9b0FY
SUPPORT_GROUP = "@TechPiroBots"
DEV_USERNAME = "@PhiloWise"
SUPPORT_GROUP_ID = -1001548130580  # Replace with your group's ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Instaloader
loader = Instaloader()

# URL validation regex
INSTAGRAM_URL_PATTERN = re.compile(r"(https?://(www\.)?instagram\.com/p/[\w-]+/)")

# Check if user is a group member
async def is_user_in_group(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(SUPPORT_GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking group membership: {e}")
        return False

# Middleware to enforce group membership
async def enforce_group_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not await is_user_in_group(context, user.id):
        keyboard = [
            [InlineKeyboardButton("🛠️ Join Support Group", url=f"https://t.me/{SUPPORT_GROUP}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ **You must join our support group before using this bot.**\n\n"
            f"🛡️ [Join Support Group]({SUPPORT_GROUP})",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return False
    return True

# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await enforce_group_membership(update, context):
        return
    
    keyboard = [
        [InlineKeyboardButton("💻 Developer", url=f"https://t.me/{DEV_USERNAME}")],
        [InlineKeyboardButton("🛠️ Support Group", url=f"https://t.me/{SUPPORT_GROUP}")],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')],
        [InlineKeyboardButton("📥 Example Download", callback_data='example_download')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "━❖ **Philo ❖ Downloader ❖** ━\n\n"
        "👋 **Welcome to the Philo Downloader Bot!**\n\n"
        "🔗 **How to Use:**\n"
        "1️⃣ Send me an Instagram post URL.\n"
        "2️⃣ Use `/download <URL>` to fetch media.\n\n"
        "📲 **Quick Links Below!**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Command: Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🏠 Home", callback_data='home')],
        [InlineKeyboardButton("💻 Developer", url=f"https://t.me/{DEV_USERNAME}")],
        [InlineKeyboardButton("🛠️ Support Group", url=f"https://t.me/{SUPPORT_GROUP}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "**ℹ️ Help Menu**\n\n"
        "📝 **Commands:**\n"
        "- `/start` → Start the bot.\n"
        "- `/download <URL>` → Download Instagram media.\n\n"
        "🔗 **Links:**\n"
        "- **Developer:** [@PhiloWise](https://t.me/{DEV_USERNAME})\n"
        "- **Support Group:** [@TechPiroBots](https://t.me/{SUPPORT_GROUP})",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Command: Download
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await enforce_group_membership(update, context):
        return

    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Please provide an Instagram post URL.\nUsage: `/download <URL>`")
        return

    url = context.args[0]
    if not INSTAGRAM_URL_PATTERN.match(url):
        await update.message.reply_text("⚠️ Invalid Instagram URL. Please provide a valid Instagram post URL.")
        return

    await update.message.reply_text("⏳ **Processing your request... Please wait.**")
    try:
        shortcode = url.split("/p/")[1].split("/")[0]
        post = Post.from_shortcode(loader.context, shortcode)

        if post.is_video:
            file_path = f"{shortcode}.mp4"
            loader.download_post(post, target=file_path)
            with open(f"{file_path}/{shortcode}.mp4", "rb") as video:
                await update.message.reply_video(video)
        else:
            file_path = f"{shortcode}.jpg"
            loader.download_post(post, target=file_path)
            with open(f"{file_path}/{shortcode}.jpg", "rb") as photo:
                await update.message.reply_photo(photo)

        await update.message.reply_text("✅ **Download Complete! Enjoy your media.**")

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Failed to download the post. Please try again later.")

# Callback Query Handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query.data == 'help':
        await help_command(update, context)
    elif query.data == 'home':
        await start(update, context)
    elif query.data == 'example_download':
        await update.callback_query.message.reply_text("🔗 Example URL: `https://instagram.com/p/ExamplePost`")
    await query.answer()

# Main function
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
