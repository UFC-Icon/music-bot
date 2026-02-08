import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8500921622:AAEbtu9pPrkDGuliFa0cXKtExdUlTC9lJyQ"  # Your bot token
ADMIN_ID = 8442398947  # Admin Telegram ID
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
AUTHORIZED_USERS = set()

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Keyboards ---
def user_keyboard():
    buttons = [
        [InlineKeyboardButton("/status", callback_data="status")],
        [InlineKeyboardButton("/cancel", callback_data="cancel")],
        [InlineKeyboardButton("/mediainfo", callback_data="mediainfo")],
    ]
    return InlineKeyboardMarkup(buttons)

def admin_keyboard():
    buttons = [
        [InlineKeyboardButton("/tasks", callback_data="tasks")],
        [InlineKeyboardButton("/allusers", callback_data="allusers")],
        [InlineKeyboardButton("/adduser", callback_data="adduser")],
        [InlineKeyboardButton("/removeuser", callback_data="removeuser")],
        [InlineKeyboardButton("/status", callback_data="status")],
        [InlineKeyboardButton("/cancel", callback_data="cancel")],
        [InlineKeyboardButton("/mediainfo", callback_data="mediainfo")],
    ]
    return InlineKeyboardMarkup(buttons)

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS and user_id != ADMIN_ID:
        await update.message.reply_text("🚫 Access denied. Ask admin")
    else:
        msg = (
            "🔥 Welcome!\n\n"
            "Send me any video/music link (YouTube, Insta, TikTok, X, Pinterest, Reddit, etc.)\n"
            "I will download and send it directly.\n\n"
            "Deployed by - Sanivaram Odu 😉😘"
        )
        kb = admin_keyboard() if user_id == ADMIN_ID else user_keyboard()
        await update.message.reply_text(msg, reply_markup=kb)

# --- Admin Commands ---
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.args:
        AUTHORIZED_USERS.add(int(context.args[0]))
        await update.message.reply_text(f"✅ Access Granted to {context.args[0]}")
    else:
        await update.message.reply_text("Usage: /adduser <tg_id>")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.args:
        AUTHORIZED_USERS.discard(int(context.args[0]))
        await update.message.reply_text(f"❌ Access Revoked from {context.args[0]}")
    else:
        await update.message.reply_text("Usage: /removeuser <tg_id>")

# --- Download Handler ---
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS and user_id != ADMIN_ID:
        await update.message.reply_text("🚫 Access denied. Ask admin")
        return

    url = update.message.text.strip()
    filename = os.path.join(DOWNLOAD_DIR, f"{user_id}_video.mp4")

    # Notify admin
    await context.bot.send_message(ADMIN_ID, f"User {user_id} is downloading: {url}")

    msg = await update.message.reply_text("⬇️ Download started...")

    cmd = [
        "N_m3u8DL-RE",
        "-i", url,
        "-o", filename,
        "--show-progress",
        "--no-merge"
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        if line.strip():
            try:
                await msg.edit_text(f"⬇️ Downloading...\n{line.strip()}")
            except:
                pass

    await msg.edit_text("✅ Download complete!")
    await update.message.reply_document(open(filename, "rb"))
    os.remove(filename)

# --- Main ---
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("removeuser", removeuser))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

print("Bot started...")
app.run_polling()

