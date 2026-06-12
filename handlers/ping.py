import time
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.formatters import get_uptime, get_ping, get_response_time, get_mention

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send ping response"""
    # Send initial "pinging" message
    start_time = time.time()
    msg = await update.message.reply_text("ᴩɪɴɢɪɴɢ...")
    
    # Calculate times
    end_time = time.time()
    received_in = round((end_time - start_time) * 1000, 2)
    
    ping = get_ping()
    response_time = get_response_time()
    uptime = get_uptime()
    user_mention = get_mention(update.effective_user)
    
    pong_text = (
        f"🏓 ᴩᴏɴɢ!\n\n"
        f"ᴩɪɴɢ: {ping}ms\n"
        f"ʀᴇꜱᴩᴏɴꜱᴇ ᴛɪᴍᴇ: {response_time}ms\n"
        f"ʀᴇᴄᴇɪᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇ ɪɴ: {received_in}ms\n"
        f"ᴜᴩᴛɪᴍᴇ: {uptime}\n\n"
        f"ᴩɪɴɢᴇᴅ ʙy: {user_mention}"
    )
    
    await msg.edit_text(
        text=pong_text,
        parse_mode='HTML'
    )

ping_handler = CommandHandler('ping', ping_command)
