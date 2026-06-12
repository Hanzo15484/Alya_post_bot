from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database import db

def admin_only():
    """Decorator to restrict command to admins and owner"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            if db.is_owner(user_id) or db.is_admin(user_id):
                return await func(update, context, *args, **kwargs)
            else:
                await update.message.reply_text("❌ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ!")
                return
        return wrapper
    return decorator

def owner_only():
    """Decorator to restrict command to owner only"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            if db.is_owner(user_id):
                return await func(update, context, *args, **kwargs)
            else:
                await update.message.reply_text("❌ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪꜱ ᴏɴʟʏ ꜰᴏʀ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ!")
                return
        return wrapper
    return decorator
