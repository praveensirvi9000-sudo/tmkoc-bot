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
import os, asyncio, json

# ================= BASIC CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))

FORCE_CHANNEL = "@Tmkocc_backup"
AUTO_DELETE_TIME = 120  # seconds

QUALITY_ORDER = ["1080p", "720p", "540p", "360p", "240p"]

# ================= TEXTS =================
INTRO_TEXT = (
    "🎬 𝗧𝗠𝗞𝗢𝗖 𝗘𝗽𝗶𝘀𝗼𝗱𝗲 𝗕𝗼𝘁\n\n"
    "नमस्ते 🙏\n\n"
    "Ye bot *Taarak Mehta Ka Ooltah Chashmah* ke fans ke liye "
    "professionally develop kiya gaya hai ❤️\n\n"
    "📺 Yahan aapko milega:\n"
    "• TMKOC ke purane aur naye episodes\n"
    "• Multiple video qualities (240p → 1080p)\n"
    "• Simple, clean aur ad-free experience\n\n"
    "📌 Use ka tareeqa:\n"
    "Bas episode number bhejo aur quality select karo.\n\n"
    "🧾 Example:\n"
    "4627\n\n"
    "⚠️ Note:\n"
    "Copyright reasons ki wajah se videos limited time ke liye hoti hain.\n"
    "Isliye episode milte hi *Saved Messages* me forward kar lena.\n\n"
    "Happy Watching 😊"
)

NOT_FOUND_TEXT = (
    "❌ Episode available nahi hai 😔\n\n"
    "Agar aap is episode ki request karna chahte ho,\n"
    "to admin se yahan contact karein 👇\n\n"
    "👉 @Admi88_bot\n\n"
    "Dhanyavaad 🙏"
)

AUTO_DELETE_TEXT = (
    "⚠️ Important Notice\n\n"
    "Copyright / safety reasons ki wajah se\n"
    "ye episode ⏳ *2 minutes* ke andar automatically delete ho jaayega.\n\n"
    "📥 Please abhi is video ko apne *Saved Messages* me forward kar lo.\n\n"
    "Support ke liye shukriya ❤️"
)

# ================= GOOGLE SHEET =================
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1cm1YSfzkJ3zVXhHpCWCxDdGPNPmhEgik09Qiw0BNLk8"

SERVICE_JSON = os.getenv("GOOGLE_SERVICE_JSON")
service_info = json.loads(SERVICE_JSON)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(service_info, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

# ================= STRICT FORCE SUB =================
async def is_verified(user_id, context):
    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

async def force_sub_message(update):
    keyboard = [[
        InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Tmkocc_backup")
    ]]
    await update.message.reply_text(
        "🔒 Bot use karne ke liye pehle channel join karna zaroori hai.\n\n"
        "Join karne ke baad fir se /start bhejein 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified(update.effective_user.id, context):
        await force_sub_message(update)
        return
    await update.message.reply_text(INTRO_TEXT)

# ================= EPISODE SEARCH =================
async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified(update.effective_user.id, context):
        await force_sub_message(update)
        return

    ep = update.message.text.strip()
    if not ep.isdigit():
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
                buttons.append([
                    InlineKeyboardButton(
                        f"🎥 {q}",
                        callback_data=f"send|{ep}|{q}"
                    )
                ])

    await update.message.reply_text(
        "🎉 Episode mil gaya!\n\nQuality select karo 👇",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= SEND VIDEO (FIXED CALLBACK) =================
async def send_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, ep, quality = q.data.split("|")

    # 🔥 message_id fresh read from sheet (NO CALLBACK OVERFLOW)
    rows = sheet.get_all_values()
    msg_id = None
    for r in rows[1:]:
        if len(r) >= 3 and r[0] == ep and r[1] == quality:
            msg_id = r[2]
            break

    if not msg_id:
        await q.message.reply_text("❌ Ye quality abhi available nahi hai.")
        return

    sent = await context.bot.copy_message(
        chat_id=q.message.chat_id,
        from_chat_id=SOURCE_CHANNEL,
        message_id=int(msg_id)
    )

    warn = await q.message.reply_text(AUTO_DELETE_TEXT)

    # 🔁 send buttons again (multi-click support)
    buttons = []
    for ql in QUALITY_ORDER:
        for r in rows[1:]:
            if r[0] == ep and r[1] == ql:
                buttons.append([
                    InlineKeyboardButton(
                        f"🎥 {ql}",
                        callback_data=f"send|{ep}|{ql}"
                    )
                ])

    if buttons:
        await context.bot.send_message(
            chat_id=q.message.chat_id,
            text="🔁 Aur quality chahiye? Neeche select karo 👇",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    await asyncio.sleep(AUTO_DELETE_TIME)
    try:
        await sent.delete()
        await warn.delete()
    except:
        pass

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(send_cb, pattern="^send"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))

    print("TMKOC Bot running (STRICT FORCE-SUB + QUALITY FIXED)")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
