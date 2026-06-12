from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from database import db
from utils.formatters import get_mention
from utils.message_utils import safe_edit_message

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send start message with welcome and buttons"""
    user = update.effective_user
    mention = get_mention(user)
    
    # Add user to database
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Get custom start text if set
    start_text = db.get_setting('start_text')
    if start_text:
        start_text = start_text.replace('{mention}', mention)
    else:
        start_text = (
            f"ʜᴇʏ {mention}\n"
            f"ɪ ᴀᴍ Alya ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɴɪᴍᴇ ᴛʜᴇᴍᴇ ʙᴏᴛ ᴛʜᴀᴛ ʜᴇʟᴘs ʏᴏᴜ "
            f"ᴛᴏ ᴩᴏꜱᴛ ʏᴏᴜʀ ᴄᴏɴᴛᴇɴᴛ ɪɴ yᴏᴜʀ ᴄʜᴀɴɴᴇʟ ⚡\n\n"
            f"────────────────────\n"
            f"➲ ʜɪᴛ ᴛʜᴇ /help ʙᴜᴛᴛᴏɴ ꜰᴏʀ ᴍᴏʀᴇ ᴅᴇᴛᴀɪʟꜱ."
        )
    
    keyboard = [
        [
            InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="about"),
            InlineKeyboardButton("Hᴇʟᴩ", callback_data="help_menu")
        ],
        [InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if start image is set
    start_image = db.get_setting('start_image')
    if start_image and start_image != 'false':
        await update.message.reply_photo(
            photo=start_image,
            caption=start_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=start_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle about button callback"""
    query = update.callback_query
    await query.answer()
    
    about_text = (
        "ʙᴏᴛ ɴᴀᴍᴇ - ᴀʟyᴀ\n"
        "ʙᴏᴛ ᴜsᴇʀɴᴀᴍᴇ - @Alya_postbot\n"
        "ᴘʏᴛʜᴏɴ ᴠᴇʀsɪᴏɴ - 3.8+\n"
        "ᴅᴀᴛᴀʙᴀsᴇ - ꜱqʟ\n"
        'ᴏᴡɴᴇʀ - <a href="t.me/Quarel7">ʜᴀɴᴢᴏ𒆜</a>\n'
        "ᴛʜɪs ʙᴏᴛ ɪs ᴏɴʟʏ ғᴏʀ ᴀɴɪᴍᴇ ғᴀʙʟᴇ"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="back_to_start"),
            InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await safe_edit_message(query, about_text, reply_markup, 'HTML')

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help button callback"""
    query = update.callback_query
    await query.answer()
    
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
    
    await safe_edit_message(query, help_text, reply_markup, 'HTML')

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button to return to start menu"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    mention = get_mention(user)
    
    start_text = db.get_setting('start_text')
    if start_text:
        start_text = start_text.replace('{mention}', mention)
    else:
        start_text = (
            f"ʜᴇʏ {mention}\n"
            f"ɪ ᴀᴍ Alya ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɴɪᴍᴇ ᴛʜᴇᴍᴇ ʙᴏᴛ ᴛʜᴀᴛ ʜᴇʟᴘs ʏᴏᴜ "
            f"ᴛᴏ ᴩᴏꜱᴛ ʏᴏᴜʀ ᴄᴏɴᴛᴇɴᴛ ɪɴ yᴏᴜʀ ᴄʜᴀɴɴᴇʟ ⚡\n\n"
            f"────────────────────\n"
            f"➲ ʜɪᴛ ᴛʜᴇ /help ʙᴜᴛᴛᴏɴ ꜰᴏʀ ᴍᴏʀᴇ ᴅᴇᴛᴀɪʟꜱ."
        )
    
    keyboard = [
        [
            InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="about"),
            InlineKeyboardButton("Hᴇʟᴩ", callback_data="help_menu")
        ],
        [InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await safe_edit_message(query, start_text, reply_markup, 'HTML')

async def close_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close/delete the message"""
    query = update.callback_query
    await query.answer()
    await query.delete_message()

async def close_with_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close with thank you alert"""
    query = update.callback_query
    await query.answer("ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜꜱɪɴɢ ᴏᴜʀ ʙᴏᴛ!", show_alert=True)
    await query.delete_message()

# Handler setup
start_handler = CommandHandler('start', start_command)
