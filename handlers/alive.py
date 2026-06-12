from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import db
from utils.formatters import get_uptime, get_ping, get_response_time, get_speed_status

async def alive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send alive/status message"""
    ping = get_ping()
    response_time = get_response_time()
    uptime = get_uptime()
    speed = get_speed_status(ping)
    
    alive_text = (
        f"ɪ'ᴍ ᴜᴩ ᴀɴᴅ ʀᴜɴɴɪɴɢ!!\n"
        f"ᴜᴩᴛɪᴍᴇ: {uptime}\n"
        f"ʀᴇsᴘᴏɴsᴇ: {response_time}ms\n"
        f"sᴛᴀᴛᴜs: {speed}"
    )
    
    # Check if alive image is set
    alive_image = db.get_setting('alive_image')
    if alive_image and alive_image != 'false':
        await update.message.reply_photo(
            photo=alive_image,
            caption=alive_text,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=alive_text,
            parse_mode='HTML'
        )

alive_handler = CommandHandler('alive', alive_command)
