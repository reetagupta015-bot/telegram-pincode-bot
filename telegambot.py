import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# CSV load
df = pd.read_csv("pincode_data.csv")

BOT_TOKEN = "8275640195:AAH8dia7edaJQmMOVdc93Ml0vmboqE_u6Iw"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📮 Welcome!\n\nSend me any PIN code (e.g. 360001) and I’ll give details."
    )

async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()

    if not pin.isdigit():
        await update.message.reply_text("❌ Please send a valid PIN code.")
        return

    result = df[df['Pincode'] == int(pin)]

    if result.empty:
        await update.message.reply_text("❌ PIN code not found.")
    else:
        row = result.iloc[0]
        reply = f"""
✅ *PIN Code Found*

📍 City: {row['City']}
🏙 District: {row['District']}
🗺 State: {row['State']}
📦 Delivery: Yes
"""
        await update.message.reply_text(reply, parse_mode="Markdown")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

app.run_polling()
