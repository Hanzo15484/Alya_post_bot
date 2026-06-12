from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from utils.decorators import owner_only
from utils.countdown import countdown_manager
import asyncio

# Conversation states
WAITING_FOR_IMAGE = 1
WAITING_FOR_TEXT = 2

@owner_only()
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    start_image = db.get_setting('start_image')
    help_image = db.get_setting('help_image')
    alive_image = db.get_setting('alive_image')
    settings_image = db.get_setting('settings_image')
    
    settings_text = (
        "⚙️ Bot Settings\n\n"
        f"sᴛᴀʀᴛ ɪᴍᴀɢᴇ: {'✅ ꜱᴇᴛ' if start_image and start_image != 'false' else '❌ ɴᴏᴛ ꜱᴇᴛ'}\n"
        f"ʜᴇʟᴩ ɪᴍᴀɢᴇ: {'✅ ꜱᴇᴛ' if help_image and help_image != 'false' else '❌ ɴᴏᴛ ꜱᴇᴛ'}\n"
        f"ᴀʟɪᴠᴇ ɪᴍᴀɢᴇ: {'✅ ꜱᴇᴛ' if alive_image and alive_image != 'false' else '❌ ɴᴏᴛ ꜱᴇᴛ'}\n"
        f"sᴇᴛᴛɪɴɢs ɪᴍᴀɢᴇ: {'✅ ꜱᴇᴛ' if settings_image and settings_image != 'false' else '❌ ɴᴏᴛ ꜱᴇᴛ'}\n\n"
        "sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴄᴏɴғɪɢᴜʀᴇ:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("sᴛᴀʀᴛ ɪᴍᴀɢᴇ", callback_data="set_start_image"),
            InlineKeyboardButton("ʜᴇʟᴩ ɪᴍᴀɢᴇ", callback_data="set_help_image")
        ],
        [
            InlineKeyboardButton("ᴀʟɪᴠᴇ ɪᴍᴀɢᴇ", callback_data="set_alive_image"),
            InlineKeyboardButton("sᴇᴛᴛɪɴɢs ɪᴍᴀɢᴇ", callback_data="set_settings_image")
        ],
        [
            InlineKeyboardButton("sᴛᴀʀᴛ ᴛᴇxᴛ", callback_data="set_start_text"),
            InlineKeyboardButton("ʜᴇʟᴩ ᴛᴇxᴛ", callback_data="set_help_text")
        ],
        [InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode='HTML')

async def set_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image setting button click"""
    query = update.callback_query
    await query.answer()
    
    setting_type = query.data.replace('set_', '')
    module_names = {
        'start_image': 'Start',
        'help_image': 'Help',
        'alive_image': 'Alive',
        'settings_image': 'Settings'
    }
    
    module_name = module_names.get(setting_type, setting_type)
    
    # Show "please wait"
    await query.edit_message_text("ᴩʟᴇᴀꜱᴇ ᴡᴀɪᴛ...")
    
    # Store setting type in user data
    context.user_data['setting_type'] = setting_type
    context.user_data['settings_input_received'] = False
    
    # Send instruction message
    instruction_text = (
        f"🖼️ {module_name} Image Settings\n\n"
        f"ɴᴏᴡ sᴇɴᴅ ᴍᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ɪɴ {module_name.lower()} ᴍᴏᴅᴜʟᴇ"
    )
    
    msg = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=instruction_text
    )
    
    # Start countdown
    context.user_data['settings_msg_id'] = msg.message_id
    context.user_data['settings_chat_id'] = msg.chat_id
    
    # Start timeout countdown in background
    asyncio.create_task(
        countdown_manager.start_settings_timeout(
            chat_id=msg.chat_id,
            message_id=msg.message_id,
            bot=context.bot,
            context=context
        )
    )
    
    return WAITING_FOR_IMAGE

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive image for settings"""
    if not update.message.photo:
        await update.message.reply_text("❌ Please send an image!")
        return WAITING_FOR_IMAGE
    
    # Mark as received
    context.user_data['settings_input_received'] = True
    
    setting_type = context.user_data.get('setting_type')
    if not setting_type:
        await update.message.reply_text("❌ Something went wrong!")
        return ConversationHandler.END
    
    # Save image file_id
    photo_file_id = update.message.photo[-1].file_id
    db.set_setting(setting_type, photo_file_id)
    
    module_names = {
        'start_image': 'Start',
        'help_image': 'Help',
        'alive_image': 'Alive',
        'settings_image': 'Settings'
    }
    module_name = module_names.get(setting_type, setting_type)
    
    # Send confirmation
    confirm_msg = await update.message.reply_text(
        f"✅ Your image has been updated successfully in {module_name}"
    )
    
    # Delete confirmation after 2 seconds
    await asyncio.sleep(2)
    await confirm_msg.delete()
    
    # Delete the user's image message
    await update.message.delete()
    
    # Delete the instruction message if possible
    try:
        msg_id = context.user_data.get('settings_msg_id')
        chat_id = context.user_data.get('settings_chat_id')
        if msg_id and chat_id:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except:
        pass
    
    # Clean up user data
    context.user_data.pop('setting_type', None)
    context.user_data.pop('settings_msg_id', None)
    context.user_data.pop('settings_chat_id', None)
    context.user_data.pop('settings_input_received', None)
    
    return ConversationHandler.END

async def set_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text setting button click"""
    query = update.callback_query
    await query.answer()
    
    setting_type = query.data.replace('set_', '')
    module_names = {
        'start_text': 'Start',
        'help_text': 'Help'
    }
    
    module_name = module_names.get(setting_type, setting_type)
    
    # Show "please wait"
    await query.edit_message_text("ᴩʟᴇᴀꜱᴇ ᴡᴀɪᴛ...")
    
    # Store setting type in user data
    context.user_data['setting_type'] = setting_type
    context.user_data['settings_input_received'] = False
    
    # Send instruction message
    instruction_text = (
        f"📝 {module_name} Text Settings\n\n"
        f"Send me the new {module_name.lower()} text. You can use {'{mention}'} for user mention."
    )
    
    msg = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=instruction_text
    )
    
    # Start countdown
    context.user_data['settings_msg_id'] = msg.message_id
    context.user_data['settings_chat_id'] = msg.chat_id
    
    asyncio.create_task(
        countdown_manager.start_settings_timeout(
            chat_id=msg.chat_id,
            message_id=msg.message_id,
            bot=context.bot,
            context=context
        )
    )
    
    return WAITING_FOR_TEXT

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive text for settings"""
    if not update.message.text:
        await update.message.reply_text("❌ Please send text!")
        return WAITING_FOR_TEXT
    
    # Mark as received
    context.user_data['settings_input_received'] = True
    
    setting_type = context.user_data.get('setting_type')
    if not setting_type:
        await update.message.reply_text("❌ Something went wrong!")
        return ConversationHandler.END
    
    # Save text
    new_text = update.message.text
    db.set_setting(setting_type, new_text)
    
    module_names = {
        'start_text': 'Start',
        'help_text': 'Help'
    }
    module_name = module_names.get(setting_type, setting_type)
    
    # Send confirmation
    confirm_msg = await update.message.reply_text(
        f"✅ {module_name} text has been updated successfully!"
    )
    
    # Delete confirmation after 2 seconds
    await asyncio.sleep(2)
    await confirm_msg.delete()
    
    # Delete the user's text message
    await update.message.delete()
    
    # Delete the instruction message if possible
    try:
        msg_id = context.user_data.get('settings_msg_id')
        chat_id = context.user_data.get('settings_chat_id')
        if msg_id and chat_id:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except:
        pass
    
    # Clean up user data
    context.user_data.pop('setting_type', None)
    context.user_data.pop('settings_msg_id', None)
    context.user_data.pop('settings_chat_id', None)
    context.user_data.pop('settings_input_received', None)
    
    return ConversationHandler.END

async def back_to_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to settings menu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("ᴩʟᴇᴀꜱᴇ ᴡᴀɪᴛ...")
    
    start_image = db.get_setting('start_image')
    help_image = db.get_setting('help_image')
    alive_image = db.get_setting('alive_image')
    settings_image = db.get_setting('settings_image')
    
    settings_text = (
        "⚙️ Bot Settings\n\n"
        f"sᴛᴀʀᴛ ɪᴍᴀɢᴇ: {'✅ ꜱᴇᴛ' if start_image and start_image != 'false' else '❌ ɴᴏᴛ ꜱᴇᴛ'}\n"
        f"ʜᴇʟᴩ ɪᴍᴀɢᴇ: {'✅ ꜱᴇᴛ' if help_image and help_image != 'false' else '❌ ɴᴏᴛ ꜱᴇᴛ'}\n"
        f"ᴀʟɪᴠᴇ ɪᴍᴀɢᴇ: {'✅ ꜱᴇᴛ' if alive_image and alive_image != 'false' else '❌ ɴᴏᴛ ꜱᴇᴛ'}\n"
        f"sᴇᴛᴛɪɴɢs ɪᴍᴀɢᴇ: {'✅ ꜱᴇᴛ' if settings_image and settings_image != 'false' else '❌ ɴᴏᴛ ꜱᴇᴛ'}\n\n"
        "sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴄᴏɴғɪɢᴜʀᴇ:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("sᴛᴀʀᴛ ɪᴍᴀɢᴇ", callback_data="set_start_image"),
            InlineKeyboardButton("ʜᴇʟᴩ ɪᴍᴀɢᴇ", callback_data="set_help_image")
        ],
        [
            InlineKeyboardButton("ᴀʟɪᴠᴇ ɪᴍᴀɢᴇ", callback_data="set_alive_image"),
            InlineKeyboardButton("sᴇᴛᴛɪɴɢs ɪᴍᴀɢᴇ", callback_data="set_settings_image")
        ],
        [
            InlineKeyboardButton("sᴛᴀʀᴛ ᴛᴇxᴛ", callback_data="set_start_text"),
            InlineKeyboardButton("ʜᴇʟᴩ ᴛᴇxᴛ", callback_data="set_help_text")
        ],
        [InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(settings_text, reply_markup=reply_markup, parse_mode='HTML')

# Conversation handler for settings
settings_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(set_image_callback, pattern='^set_.*_image$'),
        CallbackQueryHandler(set_text_callback, pattern='^set_.*_text$')
    ],
    states={
        WAITING_FOR_IMAGE: [
            MessageHandler(filters.PHOTO, receive_image),
            MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text("❌ Please send an image!"))
        ],
        WAITING_FOR_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_settings, pattern='^back_to_settings$'),
        CallbackQueryHandler(close_msg, pattern='^close_msg$')
    ]
)

settings_handler = CommandHandler('settings', settings_command)
