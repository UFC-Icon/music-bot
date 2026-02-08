import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("8338276223:AAGwQPZVADquEJePHakTUENdVii_LiPVjCM")

if not TOKEN:
    print("TOKEN not found! Add it in Koyeb Environment Variables.")
    exit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is alive and running 24/7 😤🔥")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("Bot started successfully...")

app.run_polling()

