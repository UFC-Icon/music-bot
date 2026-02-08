import subprocess
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

# ---------------- CONFIG ----------------
BOT_TOKEN = "8136973510:AAFcJy8kAcDjWFc13QuNJNrk0D3DEYxlnII"
ADMIN_ID = 8442398947  # your Telegram ID
AUTHORIZED_USERS = [ADMIN_ID]  # add more IDs if needed

# Paths in Termux
DOWNLOAD_FOLDER = "/data/data/com.termux/files/home/n_bot/downloads"
N_M3U8DL_RE_PATH = "/data/data/com.termux/files/home/n_bot/N_m3u8DL-RE"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ---------------- HELPERS ----------------
def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS

async def notify_admin(context, message):
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ You are not authorized.")
        await notify_admin(context, f"⚠️ Unauthorized user {user_id} tried to access the bot.")
        return
    await update.message.reply_text("🤖 Send me a .m3u8 or .mpd link (with optional --key if DRM).")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ You are not authorized.")
        await notify_admin(context, f"⚠️ Unauthorized user {user_id} tried to access the bot.")
        return

    url = update.message.text.strip()
    await update.message.reply_text(f"⏳ Fetching available qualities for:\n{url}")

    # Run N_m3u8DL-RE to dump info
    process = subprocess.run(
        [N_M3U8DL_RE_PATH, url, "--dump", "--json"],
        capture_output=True, text=True
    )

    try:
        info = json.loads(process.stdout)
    except Exception as e:
        await update.message.reply_text("❌ Failed to parse stream info.")
        await notify_admin(context, f"Failed to parse info for {url}: {e}")
        return

    # Get video qualities, sort highest first (up to 4K)
    video_streams = sorted(info.get("video", []), key=lambda x: int(x.get("height",0)), reverse=True)
    video_options = [str(v.get("height"))+"p" for v in video_streams if int(v.get("height",0)) <= 4320]  # upto 4K

    # Audio tracks
    audio_streams = info.get("audio", [])
    audio_options = [a.get("lang","default") for a in audio_streams]

    # Subtitles
    subtitle_streams = info.get("subtitle", [])
    subtitle_options = ["On","Off"] if subtitle_streams else ["Off"]

    # Build inline keyboard
    keyboard = []
    if video_options:
        keyboard.append([InlineKeyboardButton(v,opt_callback_data=f"video|{v}|{url}") for v in video_options])
    if audio_options:
        keyboard.append([InlineKeyboardButton(a,opt_callback_data=f"audio|{a}|{url}") for a in audio_options])
    if subtitle_options:
        keyboard.append([InlineKeyboardButton(s,opt_callback_data=f"sub|{s}|{url}") for s in subtitle_options])

    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select your options:", reply_markup=markup)

# ---------------- CALLBACK ----------------
user_choices = {}  # stores selections per user temporarily

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not is_authorized(user_id):
        await query.edit_message_text("❌ You are not authorized.")
        await notify_admin(context, f"⚠️ Unauthorized user {user_id} clicked buttons.")
        return

    data = query.data  # format: type|value|url
    type_, value, url = data.split("|",2)

    # save selection
    if user_id not in user_choices:
        user_choices[user_id] = {"video":None,"audio":None,"subtitle":None,"url":url}
    user_choices[user_id][type_] = value

    # check if all three selected
    choices = user_choices[user_id]
    if choices["video"] and choices["audio"] and choices["subtitle"]:
        await query.edit_message_text(f"✅ Starting download:\n{url}\nVideo: {choices['video']}, Audio: {choices['audio']}, Subtitles: {choices['subtitle']}")

        # build N_m3u8DL-RE command
        cmd = [N_M3U8DL_RE_PATH, choices["url"], "--workDir", DOWNLOAD_FOLDER]
        cmd += ["--video-quality", choices["video"]]
        cmd += ["--audio-lang", choices["audio"]]
        if choices["subtitle"]=="On":
            cmd += ["--subtitle"]
        
        # run download
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            if any(x in line.lower() for x in ["download","progress","finished"]):
                await context.bot.send_message(chat_id=user_id, text=line.strip())
        process.wait()

        # send latest file
        files = sorted(os.listdir(DOWNLOAD_FOLDER), key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_FOLDER, x)), reverse=True)
        if files:
            latest_file = os.path.join(DOWNLOAD_FOLDER, files[0])
            await context.bot.send_document(chat_id=user_id, document=open(latest_file,"rb"))
            await context.bot.send_message(chat_id=user_id, text="✅ Download finished!")

        await notify_admin(context, f"✅ Download finished for user {user_id}: {url}")
        user_choices.pop(user_id)  # clear choices
    else:
        await query.edit_message_text(f"Selected {type_}: {value}\nPlease select remaining options.")

# ---------------- MAIN ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_callback))

print("🤖 Secure Inline Bot is running...")
app.run_polling()

