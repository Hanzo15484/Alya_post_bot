import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from utils.formatters import get_mention, get_ist_time, format_duration

class CountdownManager:
    """Manage countdown timers for admin durations and settings timeouts"""
    
    def __init__(self):
        self.active_countdowns = {}
    
    async def start_admin_countdown(self, user_id, duration_seconds, bot, context: ContextTypes.DEFAULT_TYPE):
        """Start countdown for admin duration"""
        ist = pytz.timezone('Asia/Kolkata')
        end_time = datetime.now(ist) + timedelta(seconds=duration_seconds)
        
        # Store countdown info
        self.active_countdowns[user_id] = {
            'end_time': end_time,
            'task': None
        }
        
        # Create task
        task = asyncio.create_task(self._run_admin_countdown(user_id, duration_seconds, bot, context))
        self.active_countdowns[user_id]['task'] = task
    
    async def _run_admin_countdown(self, user_id, total_seconds, bot, context):
        """Run the countdown and notify when done"""
        try:
            await asyncio.sleep(total_seconds)
            
            # Demote admin
            db.demote_user(user_id)
            
            # Get user info
            user = db.get_user(user_id)
            if user:
                # Get promotion details
                promoted_on = user[5] if len(user) > 5 else "Unknown"
                duration = user[6] if len(user) > 6 else "Unknown"
                
                # Notify admin
                try:
                    admin_mention = f'<a href="tg://user?id={user[0]}">{user[2]}</a>'
                    
                    admin_msg = (
                        f"ʜᴇʟʟᴏ 👋 {admin_mention},\n\n"
                        f"ʏᴏᴜʀ ᴀᴅᴍɪɴ ᴩʀɪᴠɪʟᴇɢᴇꜱ ʜᴀꜱ ʙᴇᴇɴ ᴏꜰꜰɪᴄɪᴀʟʟʏ ᴇɴᴅᴇᴅ!\n\n"
                        f"ꜱᴛᴀʀᴛᴇᴅ ꜰʀᴏᴍ: {promoted_on}\n"
                        f"ᴇɴᴅ ᴏɴ: {get_ist_time()}\n\n"
                        f"ɪꜰ ʏᴏᴜ ᴡɪꜱʜ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ɪᴛ ᴩʟᴇᴀꜱᴇ ᴛᴀʟᴋ ᴛᴏ ᴍʏ ᴏᴡɴᴇʀ!"
                    )
                    
                    keyboard = [
                        [
                            InlineKeyboardButton("Oᴡɴᴇʀ", url="t.me/Quarel7"),
                            InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_alert")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await bot.send_message(
                        chat_id=user_id,
                        text=admin_msg,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Could not notify admin {user_id}: {e}")
                
                # Notify owner
                try:
                    owner_id = 5373577888
                    owner_msg = f"{admin_mention} ʜᴀꜱ ʙᴇᴇɴ ᴏꜰꜰɪᴄɪᴀʟʟʏ ᴅᴇᴍᴏᴛᴇᴅ!"
                    
                    keyboard = [[InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await bot.send_message(
                        chat_id=owner_id,
                        text=owner_msg,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Could not notify owner: {e}")
        
        finally:
            # Clean up
            if user_id in self.active_countdowns:
                del self.active_countdowns[user_id]
    
    async def start_settings_timeout(self, chat_id, message_id, bot, context):
        """Start 60-second timeout for settings image/text input"""
        countdown_msg = await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"⏳ 60s ʀᴇᴍᴀɪɴɪɴɢ"
        )
        
        for i in range(59, -1, -1):
            await asyncio.sleep(1)
            try:
                if context.user_data.get('settings_input_received'):
                    # Input was received, stop countdown
                    return True
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"⏳ {i}s ʀᴇᴍᴀɪɴɪɴɢ"
                )
            except:
                break
        
        # Timeout
        try:
            keyboard = [[InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="back_to_settings")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Timeout\nPlease use the command again",
                reply_markup=reply_markup
            )
        except:
            pass
        
        return False

countdown_manager = CountdownManager()
