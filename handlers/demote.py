from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database import db
from utils.formatters import get_mention, get_ist_time, format_duration
from utils.decorators import owner_only
from utils.countdown import countdown_manager
from datetime import datetime
import pytz

@owner_only()
async def demote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Demote an admin"""
    args = context.args
    
    if args:
        # Direct demotion with user ID
        try:
            user_id = int(args[0])
            
            # Get user info before demotion
            user = db.get_user(user_id)
            if not user or not user[4]:  # Check if user exists and is admin
                await update.message.reply_text("❌ User is not an admin!")
                return
            
            user_mention = f'<a href="tg://user?id={user[0]}">{user[2]}</a>'
            promoted_on = user[5] if user[5] else "Unknown"
            duration = user[6] if user[6] else "Permanent"
            
            # Demote user
            db.demote_user(user_id)
            
            # Stop countdown if active
            if user_id in countdown_manager.active_countdowns:
                countdown_manager.active_countdowns[user_id]['task'].cancel()
                del countdown_manager.active_countdowns[user_id]
            
            # Send confirmation to owner
            owner_msg = (
                f"✅ {user_mention} ʜᴀꜱ ʙᴇᴇɴ ᴅᴇᴍᴏᴛᴇᴅ!\n\n"
                f"Name: {user_mention}\n"
                f"ID: {user_id}\n"
                f"Was promoted on: {promoted_on}\n"
                f"Duration was: {duration}"
            )
            
            keyboard = [[InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(owner_msg, reply_markup=reply_markup, parse_mode='HTML')
            
            # Notify demoted admin
            try:
                admin_msg = (
                    f"ʜᴇʟʟᴏ 👋 {user_mention},\n\n"
                    f"yᴏᴜʀ ᴀᴅᴍɪɴ ᴩʀɪᴠɪʟᴇɢᴇꜱ ʜᴀꜱ ʙᴇᴇɴ ᴏꜰꜰɪᴄɪᴀʟʟʏ ᴇɴᴅᴇᴅ!\n\n"
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
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=admin_msg,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Could not notify demoted admin {user_id}: {e}")
        
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
    
    else:
        # Show admin list
        admins = db.get_all_admins()
        
        if not admins:
            await update.message.reply_text("No admins found!")
            return
        
        text = "**Admin list:**\nSelect an admin to view details:"
        
        # Create buttons for each admin
        keyboard = []
        for admin in admins:
            admin_name = admin[2] or f"User {admin[0]}"
            keyboard.append([InlineKeyboardButton(
                f"👤 {admin_name}",
                callback_data=f"admin_detail_{admin[0]}"
            )])
        
        keyboard.append([InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def admin_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin details when admin button is clicked"""
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split('_')[-1])
    user = db.get_user(user_id)
    
    if not user:
        await query.edit_message_text("User not found!")
        return
    
    user_mention = f'<a href="tg://user?id={user[0]}">{user[2]}</a>'
    promoted_by_user = db.get_user(user[5]) if user[5] else None
    promoted_by_mention = f'<a href="tg://user?id={user[5]}">{promoted_by_user[2] if promoted_by_user else "Unknown"}</a>' if user[5] else "Unknown"
    
    # Calculate remaining time if duration is set
    duration_display = "Permanent"
    if user[7]:  # duration_end
        try:
            ist = pytz.timezone('Asia/Kolkata')
            end_time = datetime.strptime(user[7], '%Y-%m-%d %H:%M:%S')
            end_time = ist.localize(end_time)
            now = datetime.now(ist)
            
            if end_time > now:
                remaining = end_time - now
                remaining_seconds = int(remaining.total_seconds())
                duration_display = format_duration(remaining_seconds)
            else:
                duration_display = "Expired"
        except:
            duration_display = user[6] if user[6] else "Permanent"
    
    detail_text = (
        f"👤 **Admin Details**\n\n"
        f"Name: {user_mention}\n"
        f"ID: {user[0]}\n"
        f"Promoted on: {user[5]}\n"
        f"Promoted by: {promoted_by_mention}\n"
        f"Duration: {duration_display}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("❌ Demote", callback_data=f"confirm_demote_{user[0]}"),
            InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="back_to_admin_list")
        ],
        [InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(detail_text, reply_markup=reply_markup, parse_mode='HTML')
    
    # Store admin ID for live countdown updates
    context.user_data['viewing_admin'] = user_id
    
    # Start live countdown update if duration is set
    if user[7] and duration_display != "Permanent" and duration_display != "Expired":
        await update_admin_countdown(query, user, promoted_by_mention)

async def update_admin_countdown(query, user, promoted_by_mention):
    """Update admin countdown in real-time"""
    import asyncio
    
    try:
        ist = pytz.timezone('Asia/Kolkata')
        end_time = datetime.strptime(user[7], '%Y-%m-%d %H:%M:%S')
        end_time = ist.localize(end_time)
        
        while True:
            now = datetime.now(ist)
            remaining = end_time - now
            
            if remaining.total_seconds() <= 0:
                break
            
            remaining_seconds = int(remaining.total_seconds())
            duration_display = format_duration(remaining_seconds)
            
            user_mention = f'<a href="tg://user?id={user[0]}">{user[2]}</a>'
            
            detail_text = (
                f"👤 **Admin Details**\n\n"
                f"Name: {user_mention}\n"
                f"ID: {user[0]}\n"
                f"Promoted on: {user[5]}\n"
                f"Promoted by: {promoted_by_mention}\n"
                f"Duration: {duration_display}"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("❌ Demote", callback_data=f"confirm_demote_{user[0]}"),
                    InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="back_to_admin_list")
                ],
                [InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(detail_text, reply_markup=reply_markup, parse_mode='HTML')
            except:
                break
            
            await asyncio.sleep(1)
    
    except Exception as e:
        print(f"Countdown update error: {e}")

async def confirm_demote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm demotion of admin"""
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split('_')[-1])
    user = db.get_user(user_id)
    
    if not user:
        await query.edit_message_text("User not found!")
        return
    
    user_mention = f'<a href="tg://user?id={user[0]}">{user[2]}</a>'
    
    # Demote user
    db.demote_user(user_id)
    
    # Stop countdown if active
    if user_id in countdown_manager.active_countdowns:
        countdown_manager.active_countdowns[user_id]['task'].cancel()
        del countdown_manager.active_countdowns[user_id]
    
    # Notify owner
    owner_msg = f"✅ {user_mention} ʜᴀꜱ ʙᴇᴇɴ ᴅᴇᴍᴏᴛᴇᴅ!"
    keyboard = [[InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(owner_msg, reply_markup=reply_markup, parse_mode='HTML')

async def back_to_admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to admin list"""
    query = update.callback_query
    await query.answer()
    
    admins = db.get_all_admins()
    
    if not admins:
        await query.edit_message_text("No admins found!")
        return
    
    text = "**Admin list:**\nSelect an admin to view details:"
    
    keyboard = []
    for admin in admins:
        admin_name = admin[2] or f"User {admin[0]}"
        keyboard.append([InlineKeyboardButton(
            f"👤 {admin_name}",
            callback_data=f"admin_detail_{admin[0]}"
        )])
    
    keyboard.append([InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

demote_handler = CommandHandler('demote', demote_command)
