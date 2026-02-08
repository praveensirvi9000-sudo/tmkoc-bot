from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import os, re, asyncio, json

# ================= BASIC CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

FORCE_CHANNEL = "@Tmkocc_backup"        # force subscribe
OFFICIAL_CHANNEL = "@tmkocdirect"       # user join channel

AUTO_DELETE_TIME = 120
QUALITY_ORDER = ["1080p", "720p", "540p", "360p", "240p"]

MAINTENANCE = False

# ================= TEXTS =================
INTRO_TEXT = (
    "🎬 TMKOC Episode Bot\n\n"
    "Namaste 🙏\n\n"
    "Ye bot *Taarak Mehta Ka Ooltah Chashmah* ke fans ke liye banaya gaya hai ❤️\n\n"
    "Episode number bhejo aur quality select karo.\n\n"
    "Example:\n4627\n\n"
    f"Official Channel:\n{OFFICIAL_CHANNEL}"
)

NOT_FOUND_TEXT = (
    "❌ Episode available nahi hai 😔\n\n"
    "Contact Admin option ka use karein."
)

AUTO_DELETE_TEXT = (
    "⚠️ Important Notice\n\n"
    "Copyright reasons ki wajah se\n"
    "ye video 2 minutes me delete ho jaayegi.\n\n"
    "Saved Messages me forward kar lena."
)

FOUND_TEXT = (
    "🎉 Episode mil gaya!\n\n"
    "Quality select karo 👇"
)

MAINTENANCE_TEXT = (
    "🔧 Maintenance Mode\n\n"
    "Bot abhi maintenance me hai.\n"
    "Thodi der baad try karein.\n\n"
    f"{OFFICIAL_CHANNEL}"
)

CONTACT_START_TEXT = (
    "📩 Contact Admin Mode\n\n"
    "Aap jo bhi message bhejoge,\n"
    "wo seedha admin tak jaayega.\n\n"
    "Message likhiye ✍️"
)

CONTACT_SENT_TEXT = (
    "✅ Message Sent\n\n"
    "Admin jald hi reply karega."
)

EXIT_TEXT = (
    "🚪 Contact Mode Exit\n\n"
    "Ab aap normal bot use kar sakte hain."
)

# ================= GOOGLE SHEET =================
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1cm1YSfzkJ3zVXhHpCWCxDdGPNPmhEgik09Qiw0BNLk8"
SERVICE_JSON = json.loads(os.getenv("GOOGLE_SERVICE_JSON"))

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(SERVICE_JSON, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

# ================= MEMORY =================
VERIFIED = {}
CONTACT_MODE = {}

# ================= HELPERS =================
async def is_verified(user_id, context):
    if user_id in VERIFIED:
        return True
    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, user_id)
        if member.status in ["member", "administrator", "creator"]:
            VERIFIED[user_id] = True
            return True
    except:
        pass
    return False

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if MAINTENANCE and uid != ADMIN_ID:
        await update.message.reply_text(MAINTENANCE_TEXT)
        return

    if await is_verified(uid, context):
        kb = [[InlineKeyboardButton("📩 Contact Admin", callback_data="contact")]]
        await update.message.reply_text(
            INTRO_TEXT,
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    kb = [
        [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Tmkocc_backup")],
        [InlineKeyboardButton("✅ Verify Now", callback_data="verify")]
    ]
    await update.message.reply_text(
        "Pehle channel join karo aur verify karo 👇",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= VERIFY =================
async def verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if await is_verified(q.from_user.id, context):
        await q.edit_message_text("✅ Verification successful")
        await context.bot.send_message(q.message.chat_id, INTRO_TEXT)
    else:
        await q.answer("Pehle channel join karo", show_alert=True)

# ================= CONTACT =================
async def contact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    CONTACT_MODE[uid] = True
    kb = [[InlineKeyboardButton("❌ Exit Contact Mode", callback_data="exit")]]
    await update.message.reply_text(
        CONTACT_START_TEXT,
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def contact_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await contact_cmd(update, context)

async def exit_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    CONTACT_MODE.pop(uid, None)
    await update.callback_query.edit_message_text(EXIT_TEXT)

# ================= AUTO SAVE =================
async def auto_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return
    msg = update.channel_post
    text = msg.caption or (msg.document.file_name if msg.document else "") or ""

    ep = re.search(r"Ep\s*(\d+)", text, re.IGNORECASE)
    ql = re.search(r"(240p|360p|540p|720p|1080p)", text, re.IGNORECASE)
    if ep and ql:
        sheet.append_row([ep.group(1), ql.group(1).lower(), msg.message_id])

# ================= SEARCH =================
async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if CONTACT_MODE.get(uid):
        await context.bot.send_message(
            ADMIN_ID,
            f"📩 User Message\nID: {uid}\n\n{update.message.text}"
        )
        await update.message.reply_text(CONTACT_SENT_TEXT)
        return

    ep = update.message.text.strip()
    if not ep.isdigit():
        return

    processing = await update.message.reply_text("⏳ Checking...")
    rows = sheet.get_all_values()[1:]
    data = [r for r in rows if r[0] == ep]
    await processing.delete()

    if not data:
        await update.message.reply_text(NOT_FOUND_TEXT)
        return

    buttons = []
    for q in QUALITY_ORDER:
        for r in data:
            if r[1] == q:
                buttons.append([InlineKeyboardButton(
                    f"🎥 {q}",
                    callback_data=f"send|{r[2]}"
                )])

    await update.message.reply_text(
        FOUND_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= SEND =================
async def send_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    msg_id = int(q.data.split("|")[1])
    sent = await context.bot.copy_message(
        q.message.chat_id,
        SOURCE_CHANNEL,
        msg_id
    )
    warn = await q.message.reply_text(AUTO_DELETE_TEXT)

    await asyncio.sleep(AUTO_DELETE_TIME)
    try:
        await sent.delete()
        await warn.delete()
    except:
        pass

# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MAINTENANCE
    if update.effective_user.id != ADMIN_ID:
        return

    if context.args:
        if context.args[0] == "on":
            MAINTENANCE = True
            await update.message.reply_text("Maintenance ON")
        elif context.args[0] == "off":
            MAINTENANCE = False
            await update.message.reply_text("Maintenance OFF")
        return

    rows = sheet.get_all_values()[1:]
    await update.message.reply_text(
        f"Episodes: {len(set(r[0] for r in rows))}\nFiles: {len(rows)}"
    )

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("contact", contact_cmd))

    app.add_handler(CallbackQueryHandler(verify_cb, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(contact_cb, pattern="^contact$"))
    app.add_handler(CallbackQueryHandler(exit_cb, pattern="^exit$"))
    app.add_handler(CallbackQueryHandler(send_cb, pattern="^send"))

    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))

    print("Bot running — FINAL FIXED VERSION")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
