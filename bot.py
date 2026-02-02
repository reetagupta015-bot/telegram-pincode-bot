import os
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ===============================
# LOAD MAIN PINCODE DATA
# ===============================
df = pd.read_csv("pincode_clean.csv", dtype=str)
df.columns = df.columns.str.strip().str.lower()

df['external_code'] = df['external_code'].str.strip()
df['master_pincodes_name'] = df['master_pincodes_name'].str.strip()
df['ntb urban'] = df['ntb urban'].str.strip().str.upper()
df['city'] = df['city'].str.strip()
df['state'] = df['state'].str.strip()

# ===============================
# LOAD NOT DELIVERY PINCODES
# ===============================
not_delivery_df = pd.read_csv("not_delivery_pincode.csv", dtype=str)
not_delivery_pins = set(not_delivery_df.iloc[:, 0].str.strip())

# ===============================
# BOT TOKEN
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===============================
# START COMMAND
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📮 Welcome!\n\nSend a 6-digit PIN code to check delivery availability."
    )

# ===============================
# PINCODE CHECK
# ===============================
async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()

    if not pin.isdigit() or len(pin) != 6:
        await update.message.reply_text("❌ Please send a valid 6-digit PIN code")
        return

    # ❌ FIRST PRIORITY: NOT DELIVERY
    if pin in not_delivery_pins:
        await update.message.reply_text(
            f"""
❌ *Delivery NOT Available*

📮 *PIN Code:* {pin}
🚫 *Status:* CAN'T PROCESS / NEGATIVE AREA
""",
            parse_mode="Markdown"
        )
        return

    # NORMAL CHECK
    result = df[df['external_code'] == pin]

    if result.empty:
        await update.message.reply_text("❌ PIN code not found")
        return

    row = result.iloc[0]

    if row['ntb urban'] != 'Y':
        await update.message.reply_text(
            f"""
❌ *Delivery NOT Available*

📮 *PIN Code:* {pin}
🏙 *City:* {row['city']}
🗺 *State:* {row['state']}
""",
            parse_mode="Markdown"
        )
        return

    # DELIVERY AVAILABLE
    areas = result['master_pincodes_name'].dropna().unique().tolist()
    area_text = "\n".join([f"• {a}" for a in areas])

    reply = f"""
✅ *Delivery Available*

📮 *PIN Code:* {pin}
📍 *Areas:*
{area_text}

🏙 *City:* {row['city']}
🗺 *State:* {row['state']}
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
