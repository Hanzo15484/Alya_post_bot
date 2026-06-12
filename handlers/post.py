from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from utils.decorators import admin_only
from utils.formatters import get_mention
import asyncio
from datetime import datetime
import pytz

# Conversation states
SELECTING_CHANNEL = 1
SENDING_CONTENT = 2
ADDING_BUTTONS = 3
CONFIRMING_POST = 4
SCHEDULING = 5
EDITING_CONTENT = 6

@admin_only()
async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new post"""
    channels = db.get_all_channels()
    
    if not channels:
        await update.message.reply_text("No channels added! Add channels first using /addch")
        return ConversationHandler.END
    
    # Store channels in user data
    context.user_data['channels'] = channels
    context.user_data['channel_page'] = 0
    
    # Show channel selection
    await show_channel_selection(update, context, 0)
    return SELECTING_CHANNEL

async def show_channel_selection(update, context, page):
    """Show channel selection for posting"""
    channels = context.user_data.get('channels', [])
    channels_per_page = 6  # 3 rows * 2 channels per row
    total_pages = (len(channels) + channels_per_page - 1) // channels_per_page
    
    start_idx = page * channels_per_page
    end_idx = min(start_idx + channels_per_page, len(channels))
    page_channels = channels[start_idx:end_idx]
    
    text = "Select the channel:"
    
    # Create buttons (2 per row)
    keyboard = []
    for i in range(0, len(page_channels), 2):
        row = []
        for j in range(2):
            if i + j < len(page_channels):
                channel = page_channels[i + j]
                row.append(InlineKeyboardButton(
                    channel[1][:20],
                    callback_data=f"post_to_channel_{channel[0]}"
                ))
        keyboard.append(row)
    
    # Add navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("❮ Back", callback_data=f"post_page_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ❯", callback_data=f"post_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("✖️ᴄʟᴏꜱᴇ", callback_data="cancel_post")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def post_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle post channel page navigation"""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.split('_')[-1])
    context.user_data['channel_page'] = page
    
    await show_channel_selection(update, context, page)

async def select_channel_for_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel selection for post"""
    query = update.callback_query
    await query.answer()
    
    channel_id = int(query.data.split('_')[-1])
    channel = db.get_channel(channel_id)
    
    if not channel:
        await query.edit_message_text("Channel not found!")
        return ConversationHandler.END
    
    # Store selected channel
    context.user_data['post_channel_id'] = channel_id
    context.user_data['post_channel_name'] = channel[1]
    
    text = f"Now send the content that you want to post in {channel[1]}:"
    
    keyboard = [[InlineKeyboardButton("✖️ Cancel", callback_data="cancel_post")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)
    return SENDING_CONTENT

async def receive_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive content to post"""
    message = update.message
    
    # Store content based on type
    content_data = {
        'type': None,
        'file_id': None,
        'caption': None,
        'text': None
    }
    
    if message.text:
        content_data['type'] = 'text'
        content_data['text'] = message.text
    elif message.photo:
        content_data['type'] = 'photo'
        content_data['file_id'] = message.photo[-1].file_id
        content_data['caption'] = message.caption
    elif message.video:
        content_data['type'] = 'video'
        content_data['file_id'] = message.video.file_id
        content_data['caption'] = message.caption
    elif message.document:
        content_data['type'] = 'document'
        content_data['file_id'] = message.document.file_id
        content_data['caption'] = message.caption
    elif message.animation:
        content_data['type'] = 'animation'
        content_data['file_id'] = message.animation.file_id
        content_data['caption'] = message.caption
    else:
        await message.reply_text("Unsupported content type! Please send text, photo, video, or document.")
        return SENDING_CONTENT
    
    context.user_data['post_content'] = content_data
    context.user_data['post_buttons'] = []
    
    # Show preview
    await show_post_preview(update, context)
    return ADDING_BUTTONS

async def show_post_preview(update, context):
    """Show preview of the post"""
    content = context.user_data.get('post_content')
    channel_name = context.user_data.get('post_channel_name')
    
    preview_text = f"Preview of post in {channel_name}:\n\n"
    
    if content['type'] == 'text':
        preview_text += content['text']
    else:
        preview_text += content.get('caption', '') or f"[{content['type']}]"
    
    keyboard = [
        [
            InlineKeyboardButton("Add Button", callback_data="add_button"),
            InlineKeyboardButton("Delete Post", callback_data="cancel_post")
        ],
        [
            InlineKeyboardButton("Post Now", callback_data="post_now"),
            InlineKeyboardButton("Schedule", callback_data="schedule_post")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(preview_text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(preview_text, reply_markup=reply_markup)

async def add_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add button request"""
    query = update.callback_query
    await query.answer()
    
    instruction = (
        "Send me a list of URL buttons for the message. Please use this format:\n"
        "Button text 1 - http://www.example.com/\n"
        "Button text 2 - http://www.example2.com/\n\n"
        "You can also pass an optional button color:\n"
        "Button text 1 - http://www.example.com/ - style:green\n"
        "Button text 2 - http://www.example2.com/ - style:blue\n"
        "Button text 3 - http://www.example3.com/ - style:red\n\n"
        "Use | to add up to three buttons in one row. Example:\n"
        "Button text 1 - http://www.example.com/ | Button text 2 - http://www.example2.com/\n"
        "Button text 3 - http://www.example3.com/ - style:red\n\n"
        "Choose 'Cancel' to back to creating of the post."
    )
    
    keyboard = [[InlineKeyboardButton("Cancel", callback_data="back_to_preview")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.user_data['adding_buttons'] = True
    
    await query.edit_message_text(instruction, reply_markup=reply_markup)

async def receive_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive button configuration"""
    if not context.user_data.get('adding_buttons'):
        return
    
    button_text = update.message.text
    
    if button_text.lower() == 'cancel':
        context.user_data['adding_buttons'] = False
        await show_post_preview(update, context)
        return ADDING_BUTTONS
    
    # Parse buttons
    buttons = parse_button_config(button_text)
    context.user_data['post_buttons'] = buttons
    context.user_data['adding_buttons'] = False
    
    # Show confirmation
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="post_now"),
            InlineKeyboardButton("No", callback_data="cancel_post")
        ],
        [InlineKeyboardButton("Schedule", callback_data="schedule_post")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Do you want to post it or schedule it later?",
        reply_markup=reply_markup
    )
    return CONFIRMING_POST

def parse_button_config(text):
    """Parse button configuration text"""
    buttons = []
    rows = text.strip().split('\n')
    
    for row in rows:
        row_buttons = []
        parts = row.split('|')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Parse button text, url, and style
            if ' - ' in part:
                segments = part.split(' - ')
                btn_text = segments[0].strip()
                
                # Get URL and optional style
                url_part = segments[1].strip()
                if ' - style:' in url_part:
                    url, style = url_part.split(' - style:')
                    url = url.strip()
                    style = style.strip()
                else:
                    url = url_part
                    style = None
                
                row_buttons.append({
                    'text': btn_text,
                    'url': url,
                    'style': style
                })
        
        if row_buttons:
            buttons.append(row_buttons)
    
    return buttons

async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Post content immediately"""
    query = update.callback_query
    await query.answer()
    
    await send_post(update, context)
    return ConversationHandler.END

async def schedule_post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule post for later"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "Now send the time in format\n"
        "hh:mm:ss\n"
        "Hours: hh\n"
        "Minutes: mm\n"
        "Seconds: ss"
    )
    
    await query.edit_message_text(text)
    return SCHEDULING

async def receive_schedule_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive schedule time"""
    time_str = update.message.text.strip()
    
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            total_seconds = h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = map(int, parts)
            total_seconds = m * 60 + s
        elif len(parts) == 1:
            total_seconds = int(parts[0])
        else:
            raise ValueError("Invalid format")
        
        # Store schedule info
        context.user_data['schedule_seconds'] = total_seconds
        
        # Show countdown
        await show_schedule_countdown(update, context, total_seconds)
        return ConversationHandler.END
        
    except:
        await update.message.reply_text("Invalid time format! Please use hh:mm:ss")
        return SCHEDULING

async def show_schedule_countdown(update, context, total_seconds):
    """Show schedule countdown"""
    channel_name = context.user_data.get('post_channel_name', 'Channel')
    
    # Create scheduled post in database
    ist = pytz.timezone('Asia/Kolkata')
    scheduled_time = (datetime.now(ist) + asyncio.timedelta(seconds=total_seconds)).strftime('%Y-%m-%d %H:%M:%S')
    
    content = context.user_data.get('post_content')
    buttons = context.user_data.get('post_buttons', [])
    
    db.add_post(
        channel_id=context.user_data.get('post_channel_id'),
        content_type=content['type'],
        content_data=str(content),
        caption=content.get('caption', ''),
        buttons=str(buttons),
        scheduled_time=scheduled_time,
        created_by=update.effective_user.id
    )
    
    countdown_msg = await update.message.reply_text(
        f"Your post will be sent in {total_seconds}s"
    )
    
    # Update countdown
    for i in range(total_seconds - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            keyboard = [
                [
                    InlineKeyboardButton("Send Now", callback_data="send_scheduled_now"),
                    InlineKeyboardButton("Abort", callback_data="cancel_post")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await countdown_msg.edit_text(
                f"Your post will be sent in {i}s",
                reply_markup=reply_markup
            )
        except:
            break
    
    # Send the post
    await send_post(update, context, countdown_msg)

async def send_post(update, context, message_to_edit=None):
    """Actually send the post to the channel"""
    channel_id = context.user_data.get('post_channel_id')
    content = context.user_data.get('post_content')
    buttons = context.user_data.get('post_buttons', [])
    
    # Create inline keyboard from buttons
    inline_keyboard = []
    for row_buttons in buttons:
        row = []
        for btn in row_buttons:
            row.append(InlineKeyboardButton(btn['text'], url=btn['url']))
        inline_keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard) if inline_keyboard else None
    
    try:
        if content['type'] == 'text':
            await context.bot.send_message(
                chat_id=channel_id,
                text=content['text'],
                reply_markup=reply_markup
            )
        elif content['type'] == 'photo':
            await context.bot.send_photo(
                chat_id=channel_id,
                photo=content['file_id'],
                caption=content.get('caption', ''),
                reply_markup=reply_markup
            )
        elif content['type'] == 'video':
            await context.bot.send_video(
                chat_id=channel_id,
                video=content['file_id'],
                caption=content.get('caption', ''),
                reply_markup=reply_markup
            )
        elif content['type'] == 'document':
            await context.bot.send_document(
                chat_id=channel_id,
                document=content['file_id'],
                caption=content.get('caption', ''),
                reply_markup=reply_markup
            )
        elif content['type'] == 'animation':
            await context.bot.send_animation(
                chat_id=channel_id,
                animation=content['file_id'],
                caption=content.get('caption', ''),
                reply_markup=reply_markup
            )
        
        # Notify user
        if message_to_edit:
            await message_to_edit.edit_text("✅ Post sent successfully!")
        else:
            if update.callback_query:
                await update.callback_query.edit_message_text("✅ Post sent successfully!")
            else:
                await update.message.reply_text("✅ Post sent successfully!")
    
    except Exception as e:
        error_msg = f"❌ Failed to send post: {str(e)}"
        if message_to_edit:
            await message_to_edit.edit_text(error_msg)
        else:
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            else:
                await update.message.reply_text(error_msg)

async def cancel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel post creation"""
    query = update.callback_query
    await query.answer()
    
    # Clean up user data
    keys_to_remove = ['channels', 'channel_page', 'post_channel_id', 'post_channel_name',
                      'post_content', 'post_buttons', 'adding_buttons', 'schedule_seconds']
    for key in keys_to_remove:
        context.user_data.pop(key, None)
    
    await query.edit_message_text("❌ Post cancelled!")
    await asyncio.sleep(3)
    await query.delete_message()
    
    return ConversationHandler.END

# Conversation handler for posting
post_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('post', post_command)],
    states={
        SELECTING_CHANNEL: [
            CallbackQueryHandler(select_channel_for_post, pattern='^post_to_channel_'),
            CallbackQueryHandler(post_page_callback, pattern='^post_page_'),
            CallbackQueryHandler(cancel_post, pattern='^cancel_post$')
        ],
        SENDING_CONTENT: [
            MessageHandler(filters.ALL & ~filters.COMMAND, receive_content),
            CallbackQueryHandler(cancel_post, pattern='^cancel_post$')
        ],
        ADDING_BUTTONS: [
            CallbackQueryHandler(add_button_callback, pattern='^add_button$'),
            CallbackQueryHandler(post_now, pattern='^post_now$'),
            CallbackQueryHandler(schedule_post_callback, pattern='^schedule_post$'),
            CallbackQueryHandler(cancel_post, pattern='^cancel_post$'),
            CallbackQueryHandler(lambda u, c: show_post_preview(u, c), pattern='^back_to_preview$'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buttons)
        ],
        CONFIRMING_POST: [
            CallbackQueryHandler(post_now, pattern='^post_now$'),
            CallbackQueryHandler(schedule_post_callback, pattern='^schedule_post$'),
            CallbackQueryHandler(cancel_post, pattern='^cancel_post$')
        ],
        SCHEDULING: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule_time),
            CallbackQueryHandler(cancel_post, pattern='^cancel_post$')
        ]
    },
    fallbacks=[
        CommandHandler('cancel', lambda u, c: cancel_post(u, c))
    ]
  )
