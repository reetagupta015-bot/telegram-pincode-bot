import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

DB_FILE = "pincode.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)

NEGATIVE_TABLES = [
    "sbi_negative_area",
    "cant_process",
    "au_negative_area",
    "yes_negative_area"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📮 Welcome!\n\nSend a 6-digit PIN code to check delivery (area-wise)."
    )

def is_negative(pin: str, area: str) -> bool:
    if not area:
        return True

    cur = conn.cursor()
    for table in NEGATIVE_TABLES:
        try:
            cur.execute(
                f"""
                SELECT 1 FROM {table}
                WHERE pincode = ?
                AND LOWER(area_name) = LOWER(?)
                LIMIT 1
                """,
                (pin, area)
            )
            if cur.fetchone():
                return True
        except Exception:
            continue
    return False

async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()

    if not pin.isdigit() or len(pin) != 6:
        await update.message.reply_text("❌ Invalid PIN code")
        return

    cur = conn.cursor()
    rows = cur.execute(
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
        if is_negative(pin, area) or ntb != "Y":
            non_serviceable.append(area)
        else:
            serviceable.append(area)

    reply = f"""
📮 *PIN Code:* {pin}

✅ *Delivery Available Areas:*
{chr(10).join("• " + a for a in sorted(set(serviceable))) or "—"}

❌ *Delivery NOT Available Areas:*
{chr(10).join("• " + a for a in sorted(set(non_serviceable))) or "—"}

🏙 *City:* {city}
🗺 *State:* {state}
"""
    await update.message.reply_text(reply, parse_mode="Markdown")

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable not set")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

    print("🤖 Bot started successfully")
    app.run_polling()

if __name__ == "__main__":
    main()
