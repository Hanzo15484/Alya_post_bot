from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from database import db

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = db.get_setting('help_text') or (
        "🌸 ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ:\n\n"
        "✦ ᴄʜᴀɴɴᴇʟ ᴄᴏɴᴛʀᴏʟꜱ:\n"
        "/addch - ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ\n"
        "/delch - ᴅᴇʟᴇᴛᴇ ᴄʜᴀɴɴᴇʟ\n"
        "/listch - ᴠɪᴇᴡ ᴄʜᴀɴɴᴇʟꜱ\n\n"
        "✦ ᴩᴏꜱᴛɪɴɢ ꜱyꜱᴛᴇᴍ:\n"
        "/post - ᴄʀᴇᴀᴛᴇ/ᴇᴅɪᴛ ᴄʜᴀɴɴᴇʟ ᴩᴏꜱᴛꜱ\n\n"
        "✦ ᴀᴅᴍɪɴ ᴩᴀɴᴇʟ:\n"
        "/settings - ᴍᴀɴᴀɢᴇ ʙᴏᴛ ꜱᴇᴛᴛɪɴɢꜱ\n"
        "/promote - ᴩʀᴏᴍᴏᴛᴇ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴀᴅᴍɪɴ\n"
        "/demote - ᴅᴇᴍᴏᴛᴇ ᴀᴅᴍɪɴ\n\n"
        "✦ ᴍɪꜱᴄ:\n"
        "/alive - ᴄʜᴇᴄᴋ ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ\n"
        "/ping - ʙᴏᴛ ᴜᴩᴛɪᴍᴇ\n"
        "/help - ꜱʜᴏᴡ ᴛʜɪꜱ ʜᴇʟᴩ"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="back_to_start"),
            InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if help image is set
    help_image = db.get_setting('help_image')
    if help_image and help_image != 'false':
        await update.message.reply_photo(
            photo=help_image,
            caption=help_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

help_handler = CommandHandler('help', help_command)
