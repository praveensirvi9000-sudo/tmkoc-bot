from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

FORCE_CHANNEL = "@Tmkocc_backup"      # force subscribe (OLD – unchanged)
OFFICIAL_CHANNEL = "@tmkocdirect"     # only for users (NEW)

AUTO_DELETE_TIME = 120
QUALITY_ORDER = ["1080p", "720p", "540p", "360p", "240p"]

# ================= MAINTENANCE =================
MAINTENANCE = False

# ================= INTRO TEXT (FINAL – BIG & PROFESSIONAL) =================
INTRO_TEXT = (
    "🎬 𝗧𝗠𝗞𝗢𝗖 𝗘𝗽𝗶𝘀𝗼𝗱𝗲 𝗕𝗼𝘁\n\n"
    "<b>Namaste 🙏</b>\n\n"
    "Yeh bot <b>Taarak Mehta Ka Ooltah Chashmah</b> ke sabhi fans ke liye "
    "special taur par design kiya gaya hai ❤️\n\n"
    "<b>Is bot ke features:</b>\n"
    "• Purane aur naye TMKOC episodes 📺\n"
    "• Multiple video qualities (240p – 1080p) 🎥\n"
    "• Simple, clean aur ad-free experience ✨\n\n"
    "<b>Bot ka use kaise karein?</b>\n"
    "Sirf episode number bhejiye aur apni pasand ki quality select kijiye.\n\n"
    "<b>Example:</b>\n"
    "4627\n\n"
    "<b>⚠️ Zaroori soochna:</b>\n"
    "Copyright reasons ki wajah se videos limited time ke liye available hoti hain.\n"
    "Isliye episode milte hi usse <b>Saved Messages</b> me forward kar lena.\n\n"
    "🔗 <b>Official Channel:</b>\n"
    f"{OFFICIAL_CHANNEL}\n\n"
    "Happy Watching 😊"
)

NOT_FOUND_TEXT = (
    "❌ <b>Episode available nahi hai</b> 😔\n\n"
    "Aapne jo episode manga hai wo abhi database me nahi mila.\n\n"
    "Agar request karni ho to <b>/contact</b> use karein."
)

FOUND_TEXT = (
    "🎉 <b>Good News!</b>\n\n"
    "Aapka episode mil gaya hai 😄\n\n"
    "Niche se apni pasand ki <b>video quality</b> select karein 👇"
)

AUTO_DELETE_TEXT = (
    "⚠️ <b>Important Notice</b>\n\n"
    "Copyright / safety reasons ki wajah se\n"
    "ye episode ⏳ <b>2 minutes</b> ke andar automatically delete ho jaayega.\n\n"
    "📥 Baad me dekhna ho to abhi <b>Saved Messages</b> me forward kar lo.\n\n"
    "Dhanyavaad 🙏"
)

MAINTENANCE_TEXT = (
    "🔧 <b>Maintenance Mode</b>\n\n"
    "Bot abhi maintenance me hai.\n"
    "System update aur improvements chal rahe hain ⚙️\n\n"
    "Kripya thodi der baad dobara try karein 🙏\n\n"
    f"Updates ke liye channel join rakhein:\n{OFFICIAL_CHANNEL}"
)

# ================= CONTACT ADMIN TEXT =================
CONTACT_START_TEXT = (
    "📩 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗔𝗱𝗺𝗶𝗻\n\n"
    "<b>Contact mode ON ho chuka hai.</b>\n\n"
    "Ab aap jo bhi message bhejenge,\n"
    "woh seedha admin tak pahunch jaayega 📬\n\n"
    "Apni problem ya request likhiye ✍️"
)

CONTACT_SENT_TEXT = (
    "✅ <b>Message Sent</b>\n\n"
    "Aapka message admin ko bhej diya gaya hai.\n"
    "Admin jald hi aapko jawab dega ⏳"
)

EXIT_TEXT = (
    "🚪 <b>Contact Mode Exit</b>\n\n"
    "Aap admin contact mode se bahar aa chuke hain.\n"
    "Ab aap normal tarike se bot use kar sakte hain 😊"
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
        await update.message.reply_text(MAINTENANCE_TEXT, parse_mode="HTML")
        return

    CONTACT_MODE.pop(uid, None)

    if not await is_verified(uid, context):
        keyboard = [
            [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Tmkocc_backup")],
            [InlineKeyboardButton("✅ Verify Now", callback_data="verify")]
        ]
        await update.message.reply_text(
            "🔒 Bot use karne ke liye pehle channel join karna zaroori hai.\n\n"
            "Join ke baad Verify Now par click karein 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(INTRO_TEXT, parse_mode="HTML")

# ================= VERIFY =================
async def verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if await is_verified(q.from_user.id, context):
        await q.edit_message_text("✅ Verification successful 🎉")
        await context.bot.send_message(
            q.message.chat_id,
            INTRO_TEXT,
            parse_mode="HTML"
        )
    else:
        await q.answer("❌ Pehle channel join karo", show_alert=True)

# ================= CONTACT =================
async def contact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    CONTACT_MODE[uid] = True
    await update.message.reply_text(CONTACT_START_TEXT, parse_mode="HTML")

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
            f"📩 New User Message\n\nUser ID: {uid}\n\n{update.message.text}"
        )
        await update.message.reply_text(CONTACT_SENT_TEXT, parse_mode="HTML")
        return

    ep = update.message.text.strip()
    if not ep.isdigit():
        return

    processing = await update.message.reply_text("⏳ Checking episode...")
    rows = sheet.get_all_values()[1:]
    data = [r for r in rows if r[0] == ep]
    await processing.delete()

    if not data:
        await update.message.reply_text(NOT_FOUND_TEXT, parse_mode="HTML")
        return

    buttons = []
    for q in QUALITY_ORDER:
        for r in data:
            if r[1] == q:
                buttons.append([
                    InlineKeyboardButton(f"🎥 {q}", callback_data=f"send|{r[2]}")
                ])

    await update.message.reply_text(
        FOUND_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )

# ================= SEND VIDEO =================
async def send_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    msg_id = int(q.data.split("|")[1])
    sent = await context.bot.copy_message(
        q.message.chat_id,
        SOURCE_CHANNEL,
        msg_id
    )

    warn = await q.message.reply_text(AUTO_DELETE_TEXT, parse_mode="HTML")

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
    app.add_handler(CommandHandler("contact", contact_cmd))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(CallbackQueryHandler(verify_cb, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(send_cb, pattern="^send"))

    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))

    print("Bot running — FINAL CLEAN VERSION")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
