"""Utility functions for safely editing Telegram messages"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest


async def safe_edit_message(query, text, reply_markup=None, parse_mode='HTML'):
    """
    Safely edit a message regardless of content type (text or media).
    If the message contains media and can't be edited as text, deletes it
    and sends a new message instead.
    """
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except BadRequest as e:
        if "There is no text in the message" in str(e) or "message is not modified" in str(e).lower():
            # Message is a photo/video or identical text, delete and send new
            try:
                await query.delete_message()
            except:
                pass
            
            await query.message.chat.send_message(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            raise


async def safe_edit_from_update(update: Update, text, reply_markup=None, parse_mode='HTML'):
    """
    Safely edit a message from an Update object.
    Handles both callback queries and direct message updates.
    """
    if update.callback_query:
        await safe_edit_message(update.callback_query, text, reply_markup, parse_mode)
    elif update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
