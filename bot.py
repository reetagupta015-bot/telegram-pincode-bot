import os
import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ===============================
# SQLITE CONNECTION
# ===============================
DB_FILE = "pincode.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# ===============================
# NEGATIVE TABLES (AREA-WISE)
# ===============================
NEGATIVE_TABLES = [
    "sbi_negative_area",
    "cant_process",
    "au_negative_area",
    "yes_negative_area"
]

# ===============================
# START COMMAND
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📮 Welcome!\n\nSend a *6-digit PIN code* to check delivery (area-wise).",
        parse_mode="Markdown"
    )

# ===============================
# CHECK NEGATIVE AREA (PIN + AREA)
# ===============================
def is_negative(pin, area):
    if not area:
        return True

    for table in NEGATIVE_TABLES:
        try:
            query = f"""
                SELECT 1 FROM {table}
                WHERE pincode = ?
                AND LOWER(area_name) = LOWER(?)
                LIMIT 1
            """
            cursor.execute(query, (pin, area))
            if cursor.fetchone():
                return True
        except Exception:
            continue

    return False

# ===============================
# PINCODE CHECK
# ===============================
async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()

    if not pin.isdigit() or len(pin) != 6:
        await update.message.reply_text("❌ Please send a valid 6-digit PIN code")
        return

    query = """
        SELECT master_pincodes_name, ntb_urban, city, state
        FROM pincodes
        WHERE external_code = ?
    """
    rows = cursor.execute(query, (pin,)).fetchall()

    if not rows:
        await update.message.reply_text("❌ PIN code not found")
        return

    serviceable = []
    non_serviceable = []

    city, state = rows[0][2], rows[0][3]

    for area, ntb, _, _ in rows:
        area = (area or "").strip()

        if is_negative(pin, area):
            non_serviceable.append(area)
        elif ntb == "Y":
            serviceable.append(area)
        else:
            non_serviceable.append(area)

    serviceable = sorted(set(serviceable))
    non_serviceable = sorted(set(non_serviceable))

    if not serviceable:
        await update.message.reply_text(
            f"""
❌ *Delivery NOT Available*

📮 *PIN Code:* {pin}
🚫 *Reason:* All areas are non-serviceable

🏙 *City:* {city}
🗺 *State:* {state}
""",
            parse_mode="Markdown"
        )
        return

    reply = f"""
📮 *PIN Code:* {pin}

📍 *Delivery Available Areas:*
{chr(10).join('✅ ' + a for a in serviceable)}

🚫 *Delivery NOT Available Areas:*
{chr(10).join('❌ ' + a for a in non_serviceable) if non_serviceable else '—'}

🏙 *City:* {city}
🗺 *State:* {state}
"""
    await update.message.reply_text(reply, parse_mode="Markdown")

# ===============================
# APP SETUP (v20 SAFE ✅)
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

print("🤖 Bot started successfully...")
app.run_polling()
