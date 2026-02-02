import os
import sqlite3
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
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

NEGATIVE_TABLES = [
    "sbi_negative_area",
    "cant_process",
    "au_negative_area",
    "yes_negative_area"
]

# ===============================
# COMMANDS
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📮 Welcome!\n\nSend a *6-digit PIN code* to check delivery (area-wise).",
        parse_mode="Markdown"
    )

def is_negative(pin, area):
    for table in NEGATIVE_TABLES:
        try:
            cursor.execute(
                f"""
                SELECT 1 FROM {table}
                WHERE pincode = ?
                AND LOWER(area_name) = LOWER(?)
                LIMIT 1
                """,
                (pin, area)
            )
            if cursor.fetchone():
                return True
        except:
            continue
    return False

async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()

    if not pin.isdigit() or len(pin) != 6:
        await update.message.reply_text("❌ Please send a valid 6-digit PIN code")
        return

    rows = cursor.execute(
        """
        SELECT master_pincodes_name, ntb_urban, city, state
        FROM pincodes
        WHERE external_code = ?
        """,
        (pin,)
    ).fetchall()

    if not rows:
        await update.message.reply_text("❌ PIN code not found")
        return

    serviceable, non_serviceable = [], []
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

    reply = f"""
📮 *PIN Code:* {pin}

📍 *Delivery Available Areas:*
{chr(10).join('✅ ' + a for a in serviceable) if serviceable else '—'}

🚫 *Delivery NOT Available Areas:*
{chr(10).join('❌ ' + a for a in non_serviceable) if non_serviceable else '—'}

🏙 *City:* {city}
🗺 *State:* {state}
"""
    await update.message.reply_text(reply, parse_mode="Markdown")

# ===============================
# MAIN (RENDER SAFE)
# ===============================
async def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

    print("🤖 Bot started successfully")
    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    asyncio.run(main())
