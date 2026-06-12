from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import db
from utils.formatters import get_mention, get_ist_time, parse_duration
from utils.decorators import owner_only
from utils.countdown import countdown_manager
from datetime import datetime, timedelta
import pytz

@owner_only()
async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote a user to admin"""
    args = context.args
    
    if not args:
        # Show usage
        usage_text = (
            "Use: /promote &lt;user_id&gt; &lt;duration(optional)&gt;\n\n"
            "Duration examples: 2d, 6h, 5min, 1y, 3m"
        )
        await update.message.reply_text(usage_text, parse_mode='HTML')
        return
    
    try:
        user_id = int(args[0])
        duration_str = args[1] if len(args) > 1 else None
        
        # Add user to database if not exists
        db.add_user(user_id, None, f"User {user_id}", None)
        
        # Parse duration
        duration_seconds = None
        duration_display = "Permanent"
        duration_end = None
        
        if duration_str and duration_str != '0':
            duration_seconds = parse_duration(duration_str)
            if duration_seconds:
                ist = pytz.timezone('Asia/Kolkata')
                duration_end = datetime.now(ist) + timedelta(seconds=duration_seconds)
                duration_display = f"{duration_str} (Ends: {duration_end.strftime('%Y-%m-%d %H:%M:%S')} IST)"
        
        # Promote user
        db.promote_user(
            user_id=user_id,
            promoted_by=update.effective_user.id,
            duration=duration_str if duration_str else '0',
            duration_end=duration_end.strftime('%Y-%m-%d %H:%M:%S') if duration_end else None
        )
        
        # Get user info
        promoted_user = db.get_user(user_id)
        promoter_mention = get_mention(update.effective_user)
        promoted_mention = f'<a href="tg://user?id={user_id}">{promoted_user[2] if promoted_user else "User"}</a>'
        promoted_on = get_ist_time()
        
        # Send confirmation
        confirm_text = (
            f"Admin Promoted Successfully ✔\n\n"
            f"Name: {promoted_mention}\n"
            f"User ID: {user_id}\n"
            f"Promoted by: {promoter_mention}\n"
            f"Promoted on: {promoted_on}\n"
            f"Duration: {duration_display}\n\n"
            f"Usage:\n"
            f"/promote &lt;user_id&gt; &lt;duration(optional)&gt;\n\n"
            f"Duration Format:\n"
            f"y=year, m=month, d=day, h=hour, min=minute\n"
            f"Examples: 2d, 6h, 5min, 1y, 3m"
        )
        
        await update.message.reply_text(confirm_text, parse_mode='HTML')
        
        # Start countdown if duration is set
        if duration_seconds:
            await countdown_manager.start_admin_countdown(
                user_id=user_id,
                duration_seconds=duration_seconds,
                bot=context.bot,
                context=context
            )
        
        # Notify promoted user
        try:
            notify_text = (
                f"🎉 Congratulations {promoted_mention}!\n\n"
                f"Yᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴩʀᴏᴍᴏᴛᴇᴅ ᴛᴏ ᴀᴅᴍɪɴ!\n\n"
                f"Promoted by: {promoter_mention}\n"
                f"Promoted on: {promoted_on}\n"
                f"Duration: {duration_display}"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=notify_text,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Could not notify promoted user {user_id}: {e}")
    
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

promote_handler = CommandHandler('promote', promote_command)
