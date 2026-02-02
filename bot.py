import os
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

df = pd.read_csv("pincode_data.csv")

# Clean column names
df.columns = df.columns.str.strip().str.lower()

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📮 Send PIN code")

async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()

    if not pin.isdigit():
        await update.message.reply_text("❌ Invalid PIN")
        return

    result = df[df['pincode'] == int(pin)]

    if result.empty:
        await update.message.reply_text("❌ PIN not found")
    else:
        row = result.iloc[0]
        reply = f"""
✅ *PIN Code Found*

📍 City: {row['city']}
🏙 District: {row['district']}
🗺 State: {row['state']}
"""
        await update.message.reply_text(reply, parse_mode="Markdown")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

app.run_polling()
