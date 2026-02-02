import os
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load CSV
df = pd.read_csv("pincode_data.csv")

# Clean column names
df.columns = df.columns.str.strip().str.lower()

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📮 Send PIN code (e.g. 522001)")

async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()

    if not pin.isdigit():
        await update.message.reply_text("❌ Invalid PIN code")
        return

    result = df[df['external_code'] == int(pin)]

    if result.empty:
        await update.message.reply_text("❌ PIN code not found")
    else:
        row = result.iloc[0]

        # Delivery logic
        if row['ntb urban'] == 'Y':
            delivery = "✅ Delivery Available"
        else:
            delivery = "❌ Delivery Not Available"

        reply = f"""
✅ *PIN Code Found*

📍 City: {row['city']}
🗺 State: {row['state']}
🌍 Country: {row['country']}
📦 Delivery: {delivery}
"""
        await update.message.reply_text(reply, parse_mode="Markdown")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

app.run_polling()
