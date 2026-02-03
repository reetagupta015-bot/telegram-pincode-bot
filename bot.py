import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

DB_FILE = "pincode.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)


# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📮 Send a 6-digit PIN code to check SBI & Delivery availability"
    )


# ---------------- SBI NEGATIVE AREAS ----------------
def get_sbi_negative(pin):
    cur = conn.cursor()

    try:
        rows = cur.execute("""
            SELECT negative_area
            FROM sbi_negative_area
            WHERE pin_code = ?
        """, (pin,)).fetchall()

        return [r[0] for r in rows if r[0]]

    except:
        return []


# ---------------- SBI PIN DATA ----------------
def get_sbi_pin_data(pin):
    cur = conn.cursor()

    try:
        row = cur.execute("""
            SELECT city, state
            FROM sbi_pin_code
            WHERE pin_code = ?
            LIMIT 1
        """, (pin,)).fetchone()

        return row
    except:
        return None


# ---------------- DELIVERY (IDFC / NTB) ----------------
def get_delivery_data(pin):
    cur = conn.cursor()

    try:
        row = cur.execute("""
            SELECT city, state, ntb_urban
            FROM idfc
            WHERE external_code = ?
            LIMIT 1
        """, (pin,)).fetchone()

        return row
    except:
        return None


# ---------------- MAIN PIN CHECK ----------------
async def check_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pin = update.message.text.strip()

    if not pin.isdigit() or len(pin) != 6:
        await update.message.reply_text("❌ Invalid PIN Code")
        return


    # ===== SBI CHECK =====
    sbi_data = get_sbi_pin_data(pin)
    sbi_negative = get_sbi_negative(pin)

    # ===== DELIVERY CHECK =====
    delivery_data = get_delivery_data(pin)


    # ---------- SBI RESULT ----------
    if sbi_data:
        sbi_city, sbi_state = sbi_data
        sbi_status = "✅ Available"
    else:
        sbi_city, sbi_state = "—", "—"
        sbi_status = "❌ Not Available"


    # ---------- DELIVERY RESULT ----------
    if delivery_data:
        del_city, del_state, ntb = delivery_data

        if ntb == "Y":
            delivery_status = "✅ Serviceable (PIN level)"
        else:
            delivery_status = "❌ Not Serviceable"
    else:
        del_city, del_state = "—", "—"
        delivery_status = "❌ No Data"


    # ---------- FORMAT NEGATIVE AREAS ----------
    if sbi_negative:
        negative_text = "\n".join(f"• {area}" for area in sorted(set(sbi_negative)))
    else:
        negative_text = "—"


    # ---------- FINAL MESSAGE ----------
    reply = f"""
📮 PIN Code: {pin}

🏦 SBI
Status: {sbi_status}
City: {sbi_city}
State: {sbi_state}

❌ SBI Negative Areas:
{negative_text}

🚚 Delivery Status
{delivery_status}

City: {del_city}
State: {del_state}
"""

    await update.message.reply_text(reply)


# ---------------- MAIN ----------------
def main():

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not set")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pincode))

    print("🤖 Bot started successfully")
    app.run_polling()


if __name__ == "__main__":
    main()
