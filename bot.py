import os
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load CSV as STRING (IMPORTANT)
df = pd.read_csv("pincode_data.csv", dtype=str)

# Clean column names
df.columns = df.columns.str.strip().str.lower()

# Clean pincode
df['external_code'] = df['external_code'].str.strip()

# Clean delivery column
df['ntb urban'] = df['ntb urban'].str.strip().str.upper()

# Clean area column
df['master_pincodes_name'] = df['master_pincodes_name'].str.strip()

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📮 Send PIN code")

async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()

    if not pin.isdigit():
        await update.message.reply_text("❌ Invalid PIN code")
        return

    result = df[df['external_code'] == pin]

    if result.empty:
        await update.message.reply_text("❌ PIN code not found")
    else:
        row = result.iloc[0]

        area = row['master_pincodes_name']
        city = row['city']
        state = row['state']

        delivery = "✅ Delivery Available" if row['ntb urban'] == 'Y' else "❌ Delivery Not Available"

        reply = f"""
✅ *PIN Code Found*

📮 PIN Code: {pin}
📍 Area: {area}
🏙 City: {city}
🗺 State: {state}
📦 Delivery: {delivery}
"""
        await update.message.reply_text(reply, parse_mode="Markdown")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

app.run_polling()
