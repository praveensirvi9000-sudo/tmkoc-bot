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

FORCE_CHANNEL = "@Tmkocc_backup"
AUTO_DELETE_TIME = 120  # 2 minutes

QUALITY_ORDER = ["1080p", "720p", "540p", "360p", "240p"]

# ================= TEXTS =================
INTRO_TEXT = (
    "🎬 TMKOC Episode Bot\n\n"
    "Namaste 🙏\n\n"
    "Ye bot specially *Taarak Mehta Ka Ooltah Chashmah* ke fans ke liye banaya gaya hai ❤️\n\n"
    "Yahan aapko milega:\n"
    "• TMKOC ke old & new episodes\n"
    "• Multiple video qualities (240p se 1080p tak)\n"
    "• Simple, fast aur ad-free experience\n\n"
    "📌 Use ka tareeqa:\n"
    "Bas episode number bhejo aur quality select karo.\n\n"
    "🧾 Example:\n"
    "4627\n\n"
    "⚠️ Note:\n"
    "Copyright reasons ki wajah se videos limited time ke liye hoti hain.\n"
    "Isliye episode milte hi Saved Messages me forward kar lena.\n\n"
    "Enjoy watching 😄"
)

NOT_FOUND_TEXT = (
    "❌ Episode available nahi hai 😔\n\n"
    "Aapne jo episode manga hai, wo abhi hamare database me nahi mila.\n\n"
    "📩 Agar aap is episode ki request karna chahte ho,\n"
    "to admin se contact karein 👇\n\n"
    "👉 @Admi88_bot\n\n"
    "Thanks 🙏\n"
    "TMKOC Episode Bot"
)

AUTO_DELETE_TEXT = (
    "⚠️ Important Notice\n\n"
    "Copyright aur safety reasons ki wajah se\n"
    "ye episode ⏳ *2 minutes* ke andar automatically delete ho jaayega.\n\n"
    "📥 Agar aap baad me dekhna chahte ho,\n"
    "to please is video ko abhi apne *Saved Messages* me forward kar lo.\n\n"
    "🙏 Aapke support ke liye dhanyavaad\n"
    "Enjoy watching 😊"
)

FOUND_TEXT = (
    "🎉 Good news!\n\n"
    "Aapka episode mil gaya hai 😄\n\n"
    "Ab niche se apni pasand ki *video quality* select karo 👇"
)

# ================= GOOGLE SHEET (ENV JSON) =================
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1cm1YSfzkJ3zVXhHpCWCxDdGPNPmhEgik09Qiw0BNLk8"

SERVICE_JSON = os.getenv("GOOGLE_SERVICE_JSON")
if not SERVICE_JSON:
    raise RuntimeError("GOOGLE_SERVICE_JSON env variable not set")

service_info = json.loads(SERVICE_JSON)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(service_info, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

# ================= VERIFIED USERS (MEMORY) =================
VERIFIED = {}

# ================= FORCE SUBSCRIBE CHECK =================
async def is_verified(user_id, context):
    if str(user_id) in VERIFIED:
        return True
    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, user_id)
        if member.status in ["member", "administrator", "creator"]:
            VERIFIED[str(user_id)] = True
            return True
    except:
        pass
    return False

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if await is_verified(user_id, context):
        await update.message.reply_text(INTRO_TEXT)
        return

    keyboard = [
        [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Tmkocc_backup")],
        [InlineKeyboardButton("✅ Verify Now", callback_data="verify")]
    ]

    await update.message.reply_text(
        "🔒 Bot use karne ke liye pehle channel join karna zaroori hai.\n\n"
        "1️⃣ Niche diye gaye button se channel join karo\n"
        "2️⃣ Join ke baad **Verify Now** par click karo\n\n"
        "Verify hote hi aapko poora bot access mil jaayega 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= VERIFY CALLBACK =================
async def verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if await is_verified(q.from_user.id, context):
        await q.edit_message_text(
            "✅ Verification successful 🎉\n\n"
            "Aap successfully verify ho chuke ho."
        )
        await context.bot.send_message(
            chat_id=q.message.chat_id,
            text=INTRO_TEXT
        )
    else:
        await q.answer("❌ Pehle channel join karo", show_alert=True)

# ================= AUTO SAVE FROM SOURCE CHANNEL =================
async def auto_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return

    msg = update.channel_post
    text = msg.caption or (msg.document.file_name if msg.document else "") or ""

    ep_m = re.search(r"Ep\s*(\d+)", text, re.IGNORECASE)
    q_m = re.search(r"(240p|360p|540p|720p|1080p)", text, re.IGNORECASE)

    if not ep_m or not q_m:
        return

    ep = ep_m.group(1)
    quality = q_m.group(1).lower()
    msg_id = msg.message_id

    sheet.append_row([ep, quality, msg_id])
    print(f"Saved Ep{ep} [{quality}]")

# ================= USER SEARCH =================
async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ep = update.message.text.strip()
    if not ep.isdigit():
        return

    if not await is_verified(update.effective_user.id, context):
        await start(update, context)
        return

    processing = await update.message.reply_text("⏳ Episode check ho raha hai...")
    await asyncio.sleep(1)

    rows = sheet.get_all_values()
    data = [r for r in rows[1:] if len(r) >= 3 and r[0] == ep]

    await processing.delete()

    if not data:
        await update.message.reply_text(NOT_FOUND_TEXT)
        return

    buttons = []
    for q in QUALITY_ORDER:
        for r in data:
            if r[1] == q:
                buttons.append(
                    [InlineKeyboardButton(
                        f"🎥 {q}",
                        callback_data=f"send|{ep}|{q}|{r[2]}"
                    )]
                )

    await update.message.reply_text(
        FOUND_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= SEND VIDEO + AUTO DELETE =================
async def send_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, ep, quality, msg_id = q.data.split("|")

    sent = await context.bot.copy_message(
        chat_id=q.message.chat_id,
        from_chat_id=SOURCE_CHANNEL,
        message_id=int(msg_id)
    )

    warn = await q.message.reply_text(AUTO_DELETE_TEXT)

    await asyncio.sleep(AUTO_DELETE_TIME)
    try:
        await sent.delete()
        await warn.delete()
    except:
        pass

# ================= ADMIN PANEL =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    rows = sheet.get_all_values()[1:]
    total_eps = len(set(r[0] for r in rows if len(r) >= 1))
    total_files = len(rows)

    await update.message.reply_text(
        "👑 Admin Panel\n\n"
        f"Total Episodes: {total_eps}\n"
        f"Total Files: {total_files}"
    )

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(verify_cb, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(send_cb, pattern="^send"))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))

    print("Bot running (Google Sheet DB • ENV JSON • Stable)")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
