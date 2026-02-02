import os
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ===============================
# LOAD CLEAN CSV (ALL AS STRING)
# ===============================
df = pd.read_csv("pincode_clean.csv", dtype=str)

# ===============================
# CLEAN COLUMN NAMES
# ===============================
df.columns = df.columns.str.strip().str.lower()

# ===============================
# CLEAN IMPORTANT COLUMNS
# ===============================
# PINCODE
df['external_code'] = df['external_code'].str.strip()

# AREA / POST OFFICE NAME
df['master_pincodes_name'] = df['master_pincodes_name'].str.strip()

# DELIVERY FLAG
df['ntb urban'] = df['ntb urban'].str.strip().str.upper()

# CITY / STATE
df['city'] = df['city'].str.strip()
df['state'] = df['state'].str.strip()

# ===============================
# BOT TOKEN (FROM RENDER ENV)
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===============================
# START COMMAND
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📮 Welcome!\n\nSend a 6-digit PIN code (e.g. 110086)"
    )

# ===============================
# PINCODE CHECK HANDLER
# ===============================
async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()

    # Validate PIN
    if not pin.isdigit() or len(pin) != 6:
        await update.message.reply_text("❌ Please send a valid 6-digit PIN code")
        return

    # Search PINCODE (STRING MATCH)
    result = df[df['external_code'] == pin]

    if result.empty:
        await update.message.reply_text("❌ PIN code not found")
        return

    row = result.iloc[0]

    # DELIVERY STATUS
    delivery = "✅ Delivery Available" if row['ntb urban'] == 'Y' else "❌ Delivery Not Available"

    # ALL AREAS FOR THIS PIN
    areas = result['master_pincodes_name'].dropna().unique().tolist()
    area_text = "\n".join([f"• {a}" for a in areas])

    reply = f"""
✅ *PIN Code Found*

📮 *PIN Code:* {pin}
📍 *Areas:*
{area_text}

🏙 *City:* {row['city']}
🗺 *State:* {row['state']}
📦 *Delivery:* {delivery}
"""
    await update.message.reply_text(reply, parse_mode="Markdown")

# ===============================
# APP SETUP
# ===============================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

# ===============================
# RUN BOT
# ===============================
app.run_polling()
