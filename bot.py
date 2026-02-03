import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

DB_FILE = "pincode.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)


# ---------------- SBI PIN ----------------
def get_sbi_pin(pin):
    cur = conn.cursor()

    return cur.execute(
        """
        SELECT city, state
        FROM sbi_pin_code
        WHERE pin_code = ?
        LIMIT 1
        """,
        (pin,)
    ).fetchone()


# ---------------- SBI NEGATIVE ----------------
def get_sbi_negative(pin):
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
        COALESCE(area_name, negative_area_policy_mmi)
        FROM sbi_negative_area
        WHERE pin_code = ?
        """,
        (pin,)
    ).fetchall()

    return [r[0] for r in rows if r[0]]


# ---------------- CANT PROCESS ----------------
def is_cant_process(pin):
    cur = conn.cursor()

    row = cur.execute(
        """
        SELECT 1
        FROM cant_process
        WHERE pin_code = ?
        LIMIT 1
        """,
        (pin,)
    ).fetchone()

    return bool(row)


# ---------------- BOT MAIN ----------------
async def check_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pin = update.message.text.strip()

    if not pin.isdigit() or len(pin) != 6:
        await update.message.reply_text("❌ Invalid PIN")
        return


    # SBI PIN
    sbi = get_sbi_pin(pin)

    # SBI NEGATIVE
    negative = get_sbi_negative(pin)

    # CANT PROCESS
    cant = is_cant_process(pin)


    msg = f"📮 PIN Code: {pin}\n\n"


    # -------- SBI RESULT --------
    if sbi:
        msg += "🏦 SBI\n"
        msg += "Status: ✅ Available\n"
        msg += f"City: {sbi[0]}\n"
        msg += f"State: {sbi[1]}\n\n"
    else:
        msg += "🏦 SBI\n"
        msg += "Status: ❌ Not Available\n\n"


    # -------- NEGATIVE AREAS --------
    msg += "❌ SBI Negative Areas:\n"

    if negative:
        for a in sorted(set(negative)):
            msg += f"• {a}\n"
    else:
        msg += "—\n"


    # -------- CANT PROCESS --------
    msg += "\n⚠ Cant Process Status:\n"

    if cant:
        msg += "❌ This PIN is marked as CANT PROCESS"
    else:
        msg += "✅ This PIN is allowed"


    await update.message.reply_text(msg)


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send 6 digit PIN code")


# ---------------- MAIN ----------------
def main():

    token = os.environ.get("BOT_TOKEN")

    if not token:
        raise RuntimeError("BOT_TOKEN not set")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pin))

    print("🤖 SBI Checker Running")
    app.run_polling()


if __name__ == "__main__":
    main()
