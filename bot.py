import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ===============================
# SQLITE CONNECTION
# ===============================
DB_FILE = "pincode.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)

# ===============================
# NEGATIVE TABLES (ALL)
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
        "📮 Welcome!\n\nSend a 6-digit PIN code to check delivery availability (area-wise)."
    )

# ===============================
# CHECK IF AREA IS NEGATIVE
# ===============================
def is_negative(pin, area):
    for table in NEGATIVE_TABLES:
        try:
            # try both pin-only & pin+area logic safely
            q = f"""
            SELECT 1 FROM {table}
            WHERE pincode = ?
            LIMIT 1
            """
            if conn.execute(q, (pin,)).fetchone():
                return True
        except:
            pass
    return False

# ===============================
# PINCODE CHECK (FINAL)
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
    rows = conn.execute(query, (pin,)).fetchall()

    if not rows:
        await update.message.reply_text("❌ PIN code not found")
        return

    serviceable = []
    non_serviceable = []

    city, state = rows[0][2], rows[0][3]

    for area, ntb, _, _ in rows:
        area = area.strip()

        # Negative override
        if is_negative(pin, area):
            non_serviceable.append(area)
            continue

        if ntb == "Y":
            serviceable.append(area)
        else:
            non_serviceable.append(area)

    # Remove duplicates
    serviceable = sorted(set(serviceable))
    non_serviceable = sorted(set(non_serviceable))

    # If no serviceable areas
    if not serviceable:
        await update.message.reply_text(
            f"""
❌ *Delivery NOT Available*

📮 *PIN Code:* {pin}
🚫 *Reason:* No serviceable areas

🏙 *City:* {city}
🗺 *State:* {state}
""",
            parse_mode="Markdown"
        )
        return

    # Prepare text
    serviceable_text = "\n".join([f"✅ {a}" for a in serviceable])
    non_serviceable_text = (
        "\n".join([f"❌ {a}" for a in non_serviceable])
        if non_serviceable else
        "—"
    )

    reply = f"""
📮 *PIN Code:* {pin}

📍 *Delivery Available Areas:*
{serviceable_text}

🚫 *Delivery NOT Available Areas:*
{non_serviceable_text}

🏙 *City:* {city}
🗺 *State:* {state}
"""
    await update.message.reply_text(reply, parse_mode="Markdown")

# ===============================
# APP SETUP
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

app.run_polling()
