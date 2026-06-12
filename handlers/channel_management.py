from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database import db
from utils.decorators import admin_only, owner_only
from utils.formatters import get_mention
import asyncio

# Temporary storage for waiting channel operations
waiting_for = {}

@admin_only()
async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a channel to the bot"""
    user_id = update.effective_user.id
    waiting_for[user_id] = 'add_channel'
    
    text = (
        "ꜰᴏʀᴡᴀʀᴅ ᴀ ᴍᴇꜱꜱᴀɢᴇ ꜰʀᴏᴍ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴀᴅᴅ.\n"
        "ʏᴏᴜ ᴄᴀɴ ᴀʟꜱᴏ ꜱᴇɴᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ.\n\n"
        "ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴛʜᴀᴛ ᴛʜɪꜱ ʙᴏᴛ ɪꜱ ᴀᴅᴅᴇᴅ ᴀꜱ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ."
    )
    
    keyboard = [[InlineKeyboardButton("Cᴀɴᴄᴇʟ ✖️", callback_data="cancel_add_channel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def cancel_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel adding channel"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id in waiting_for:
        del waiting_for[user_id]
    
    await query.edit_message_text("❌ Process cancelled!")
    await asyncio.sleep(3)
    await query.delete_message()

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle forwarded message or channel ID for add/del operations"""
    user_id = update.effective_user.id
    
    if user_id not in waiting_for:
        return
    
    action = waiting_for[user_id]
    message = update.message
    
    channel_id = None
    channel_name = None
    channel_username = None
    invite_link = None
    
    # Check if it's a forwarded message from a channel
    if message.forward_from_chat and message.forward_from_chat.type == 'channel':
        channel = message.forward_from_chat
        channel_id = channel.id
        channel_name = channel.title
        channel_username = channel.username
        if channel_username:
            invite_link = f"https://t.me/{channel_username}"
        else:
            invite_link = f"https://t.me/c/{str(channel_id).replace('-100', '')}"
    
    # Check if it's a channel ID (text message with numbers and possibly minus)
    elif message.text:
        try:
            channel_id = int(message.text.strip())
            # Try to get channel info
            try:
                chat = await context.bot.get_chat(channel_id)
                channel_name = chat.title
                channel_username = chat.username
                if channel_username:
                    invite_link = f"https://t.me/{channel_username}"
                else:
                    invite_link = chat.invite_link or f"https://t.me/c/{str(channel_id).replace('-100', '')}"
            except:
                await message.reply_text("❌ Cannot access channel. Make sure bot is admin in that channel!")
                del waiting_for[user_id]
                return
        except ValueError:
            await message.reply_text("❌ Invalid channel ID!")
            del waiting_for[user_id]
            return
    
    if not channel_id:
        await message.reply_text("❌ Please forward a message from a channel or send a valid channel ID!")
        return
    
    if action == 'add_channel':
        # Start verification animation
        status_msg = await message.reply_text("ᴠᴇʀɪꜰʏɪɴɢ")
        
        for dots in [".", "..", "...", "...."]:
            await asyncio.sleep(0.8)
            await status_msg.edit_text(f"ᴠᴇʀɪꜰʏɪɴɢ{dots}")
        
        await asyncio.sleep(0.5)
        
        # Verify if bot can access the channel
        try:
            # Try to get chat to verify
            await context.bot.get_chat(channel_id)
            
            # Add to database
            db.add_channel(
                channel_id=channel_id,
                channel_name=channel_name,
                channel_username=channel_username,
                added_by=user_id,
                invite_link=invite_link
            )
            
            await status_msg.edit_text("✅ ᴠᴇʀɪꜰɪᴇᴅ")
            await asyncio.sleep(0.5)
            await status_msg.edit_text(f"{channel_name} ᴀᴅᴅᴇᴅ!")
            
            # Delete after 5 seconds
            await asyncio.sleep(5)
            await status_msg.delete()
            
        except Exception as e:
            await status_msg.edit_text("❌ ɴᴏᴛ ᴠᴇʀɪꜰɪᴇᴅ")
            await asyncio.sleep(5)
            await status_msg.delete()
    
    elif action == 'del_channel':
        # Start verification animation
        status_msg = await message.reply_text("ᴠᴇʀɪꜰʏɪɴɢ")
        
        for dots in [".", "..", "...", "...."]:
            await asyncio.sleep(0.8)
            await status_msg.edit_text(f"ᴠᴇʀɪꜰʏɪɴɢ{dots}")
        
        await asyncio.sleep(0.5)
        
        # Check if channel exists in database
        channel = db.get_channel(channel_id)
        if channel:
            await status_msg.edit_text("✅ ᴠᴇʀɪꜰɪᴇᴅ")
            await asyncio.sleep(0.5)
            
            db.remove_channel(channel_id)
            await status_msg.edit_text(f"{channel_name or channel[1]} ʜᴀꜱ ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ʙᴏᴛ!")
            
            await asyncio.sleep(5)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ ᴄʜᴀɴɴᴇʟ ɴᴏᴛ ꜰᴏᴜɴᴅ")
            await asyncio.sleep(5)
            await status_msg.delete()
    
    # Clean up
    del waiting_for[user_id]

@owner_only()
async def del_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a channel from the bot"""
    user_id = update.effective_user.id
    waiting_for[user_id] = 'del_channel'
    
    text = "Now forward a message from added channel or send channel id."
    
    await update.message.reply_text(text)

@owner_only()
async def list_channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all added channels"""
    channels = db.get_all_channels()
    
    if not channels:
        await update.message.reply_text("No channels added!")
        return
    
    # Store channels in user data for pagination
    context.user_data['all_channels'] = channels
    context.user_data['channel_page'] = 0
    
    await show_channel_page(update, context, 0)

async def show_channel_page(update, context, page):
    """Show a page of channels"""
    channels = context.user_data.get('all_channels', [])
    channels_per_page = 12  # 6 rows * 2 channels per row
    total_pages = (len(channels) + channels_per_page - 1) // channels_per_page
    
    start_idx = page * channels_per_page
    end_idx = min(start_idx + channels_per_page, len(channels))
    page_channels = channels[start_idx:end_idx]
    
    text = f"List of all added channels:\n\n{len(channels)} channels"
    
    # Create buttons (2 per row)
    keyboard = []
    for i in range(0, len(page_channels), 2):
        row = []
        for j in range(2):
            if i + j < len(page_channels):
                channel = page_channels[i + j]
                channel_name = channel[1][:20]  # Truncate long names
                row.append(InlineKeyboardButton(
                    channel_name,
                    callback_data=f"channel_detail_{channel[0]}"
                ))
        keyboard.append(row)
    
    # Add navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("❮ Back", callback_data=f"channel_page_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ❯", callback_data=f"channel_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def channel_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel page navigation"""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.split('_')[-1])
    context.user_data['channel_page'] = page
    
    await show_channel_page(update, context, page)

async def channel_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel details"""
    query = update.callback_query
    await query.answer()
    
    channel_id = int(query.data.split('_')[-1])
    channel = db.get_channel(channel_id)
    
    if not channel:
        await query.edit_message_text("Channel not found!")
        return
    
    detail_text = (
        f"📢 Channel Details\n\n"
        f"Channel name: {channel[1]}\n"
        f"ID: {channel[0]}\n"
        f"Added on: {channel[3]}\n"
        f"Invite link: {channel[5] or 'Not available'}"
    )
    
    keyboard = [
        [InlineKeyboardButton("✖️ Remove", callback_data=f"confirm_remove_ch_{channel_id}")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data=f"channel_page_{context.user_data.get('channel_page', 0)}")],
        [InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="close_msg")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(detail_text, reply_markup=reply_markup)

async def confirm_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm channel removal"""
    query = update.callback_query
    await query.answer()
    
    channel_id = int(query.data.split('_')[-1])
    channel = db.get_channel(channel_id)
    
    if not channel:
        await query.edit_message_text("Channel not found!")
        return
    
    text = f"Are you sure you want to remove {channel[1]}?"
    
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data=f"remove_ch_{channel_id}"),
            InlineKeyboardButton("No", callback_data=f"channel_detail_{channel_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove channel from database"""
    query = update.callback_query
    
    channel_id = int(query.data.split('_')[-1])
    channel = db.get_channel(channel_id)
    channel_name = channel[1] if channel else "Unknown"
    
    db.remove_channel(channel_id)
    
    await query.answer(f"{channel_name} has been removed!", show_alert=True)
    
    # Refresh channel list
    channels = db.get_all_channels()
    context.user_data['all_channels'] = channels
    context.user_data['channel_page'] = 0
    
    await show_channel_page(update, context, 0)

add_channel_handler = CommandHandler('addch', add_channel_command)
del_channel_handler = CommandHandler('delch', del_channel_command)
list_channels_handler = CommandHandler('listch', list_channels_command)
