import os
import sqlite3
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)

DB_FILE = "pincode_final.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)

ADMIN_IDS = [8251246853]


# ---------------- USER DATABASE ----------------
def init_db():
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiry INTEGER
    )
    """)

    conn.commit()


def add_trial(user_id):
    cur = conn.cursor()

    user = cur.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if not user:
        expiry = int(time.time()) + 86400  # 1 day trial
        cur.execute("INSERT INTO users VALUES (?, ?)", (user_id, expiry))
        conn.commit()
        return True

    return False


def check_access(user_id):
    cur = conn.cursor()

    user = cur.execute(
        "SELECT expiry FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if not user:
        return False

    return user[0] > int(time.time())


# ---------------- ACCESS REQUEST ----------------
async def request_access(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])
    user = query.from_user

    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]
    ]

    for admin in ADMIN_IDS:
        await context.bot.send_message(
            admin,
            f"🔐 ACCESS REQUEST\n\n👤 {user.first_name}\n🆔 {user_id}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await query.edit_message_text("Request sent to admin")


# ---------------- ADMIN APPROVE ----------------
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    action, user_id = query.data.split("_")
    user_id = int(user_id)

    if query.from_user.id not in ADMIN_IDS:
        return

    if action == "approve":
        expiry = int(time.time()) + 30 * 86400

        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO users VALUES (?, ?)",
            (user_id, expiry)
        )
        conn.commit()

        await context.bot.send_message(user_id, "✅ Access approved for 30 days")
        await query.edit_message_text("User approved")

    elif action == "reject":
        await context.bot.send_message(user_id, "❌ Access rejected")
        await query.edit_message_text("User rejected")


# ---------------- SBI FUNCTIONS ----------------
def get_sbi_pin(pin):
    cur = conn.cursor()
    return cur.execute(
        "SELECT city, state FROM sbi_pin_code WHERE pin_code=?",
        (pin,)
    ).fetchone()


def get_sbi_negative(pin):
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT area_name FROM sbi_negative_area WHERE pin_code=?",
        (pin,)
    ).fetchall()
    return [r[0] for r in rows if r[0]]


def is_cant_process(pin):
    cur = conn.cursor()
    return bool(cur.execute(
        "SELECT 1 FROM s8 WHERE pin_code=?",
        (pin,)
    ).fetchone())


# ---------------- PIN CHECK ----------------
async def check_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # Access check
    if not check_access(user_id):
        keyboard = [
            [InlineKeyboardButton("🔐 Request Access", callback_data=f"req_{user_id}")]
        ]

        await update.message.reply_text(
            "❌ Free Trial Expired",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    pin = update.message.text.strip()

    if not pin.isdigit() or len(pin) != 6:
        await update.message.reply_text("❌ Invalid PIN")
        return

    sbi = get_sbi_pin(pin)
    negative = get_sbi_negative(pin)
    cant = is_cant_process(pin)

    msg = f"📮 PIN Code: {pin}\n\n"

    # -------- SBI RESULT --------
    if sbi:
        msg += "🏦 SBI\n"
        msg += f"City: {sbi[0]}\n"
        msg += f"State: {sbi[1]}\n\n"
    else:
        msg += "🏦 SBI\n"
        msg += "Status: ❌ Not Available\n\n"

    # -------- DELIVERY DECISION --------
    if not sbi:
        delivery_status = "❌ Not Deliverable"
    elif negative or cant:
        delivery_status = "⚠ Risk / Possibly Not Deliverable"
    else:
        delivery_status = "✅ Deliverable"

    msg += f"🚚 Delivery Status: {delivery_status}\n\n"

    # -------- NEGATIVE AREAS --------
    msg += "❌ SBI Negative Areas:\n"

    if negative:
        for area in sorted(set(negative)):
            msg += f"• {area}\n"
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

    user = update.effective_user
    user_id = user.id
    name = user.first_name
    username = user.username or "No Username"

    new_user = add_trial(user_id)

    if new_user:

        welcome_msg = f"""
🏦 Welcome to SBI PinChecker Bot 🏦

👤 {name}
🆔 Your ID: {user_id}

🎁 Free Trial Activated (1 Day)

🔥 BOT BENEFITS
• Fast PIN Delivery Check
• Negative Area Detection
• Cant Process Detection
"""

        await update.message.reply_text(welcome_msg)

        admin_msg = f"""
🆕 NEW USER JOINED

👤 Name: {name}
🆔 UserID: {user_id}
📛 @{username}
"""

        for admin in ADMIN_IDS:
            await context.bot.send_message(admin, admin_msg)

        return

    await update.message.reply_text("📮 Send 6 digit PIN code")


# ---------------- MAIN ----------------
def main():

    init_db()

    token = os.environ.get("BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(request_access, pattern="^req_"))
    app.add_handler(CallbackQueryHandler(handle_admin, pattern="^(approve|reject)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_pin))

    print("🤖 SBI Checker Running")
    app.run_polling()


if __name__ == "__main__":
    main()
