import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from database import db
from config import BOT_TOKEN
from utils.countdown import countdown_manager

# Import handlers
from handlers.start import start_command, about_callback, help_callback, back_to_start, close_msg, close_with_alert
from handlers.help import help_command
from handlers.alive import alive_command
from handlers.ping import ping_command
from handlers.promote import promote_command
from handlers.demote import demote_command, admin_detail_callback, confirm_demote_callback, back_to_admin_list
from handlers.settings import settings_command, settings_conv_handler, back_to_settings
from handlers.channel_management import (
    add_channel_command, del_channel_command, list_channels_command,
    cancel_add_channel, handle_channel_message, channel_page_callback,
    channel_detail_callback, confirm_remove_channel, remove_channel
)
from handlers.post import post_conv_handler

# Temporary storage for add/del channel operations
from handlers.channel_management import waiting_for

async def handle_message(update: Update, context):
    """Handle all incoming messages"""
    user_id = update.effective_user.id
    
    # Check if user is waiting for channel operation
    if user_id in waiting_for:
        await handle_channel_message(update, context)
        return
    
    # Default response
    await update.message.reply_text("Use /help to see available commands!")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('alive', alive_command))
    application.add_handler(CommandHandler('ping', ping_command))
    application.add_handler(CommandHandler('promote', promote_command))
    application.add_handler(CommandHandler('demote', demote_command))
    application.add_handler(CommandHandler('settings', settings_command))
    application.add_handler(CommandHandler('addch', add_channel_command))
    application.add_handler(CommandHandler('delch', del_channel_command))
    application.add_handler(CommandHandler('listch', list_channels_command))
    
    # Add conversation handlers
    application.add_handler(settings_conv_handler)
    application.add_handler(post_conv_handler)
    
    # Add callback query handlers
    # Start menu callbacks
    application.add_handler(CallbackQueryHandler(about_callback, pattern='^about$'))
    application.add_handler(CallbackQueryHandler(help_callback, pattern='^help_menu$'))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    application.add_handler(CallbackQueryHandler(close_msg, pattern='^close_msg$'))
    application.add_handler(CallbackQueryHandler(close_with_alert, pattern='^close_alert$'))
    
    # Demote callbacks
    application.add_handler(CallbackQueryHandler(admin_detail_callback, pattern='^admin_detail_'))
    application.add_handler(CallbackQueryHandler(confirm_demote_callback, pattern='^confirm_demote_'))
    application.add_handler(CallbackQueryHandler(back_to_admin_list, pattern='^back_to_admin_list$'))
    
    # Settings callbacks
    application.add_handler(CallbackQueryHandler(back_to_settings, pattern='^back_to_settings$'))
    
    # Channel management callbacks
    application.add_handler(CallbackQueryHandler(cancel_add_channel, pattern='^cancel_add_channel$'))
    application.add_handler(CallbackQueryHandler(channel_page_callback, pattern='^channel_page_'))
    application.add_handler(CallbackQueryHandler(channel_detail_callback, pattern='^channel_detail_'))
    application.add_handler(CallbackQueryHandler(confirm_remove_channel, pattern='^confirm_remove_ch_'))
    application.add_handler(CallbackQueryHandler(remove_channel, pattern='^remove_ch_'))
    
    # Add message handler for non-command messages
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Start bot
    print("🤖 Bot is starting...")
    print("✅ Bot is now running!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
