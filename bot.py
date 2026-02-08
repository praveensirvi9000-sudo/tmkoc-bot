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

FORCE_CHANNEL = "@Tmkocc_backup"
OFFICIAL_CHANNEL = "@tmkocdirect"

AUTO_DELETE_TIME = 120
QUALITY_ORDER = ["1080p", "720p", "540p", "360p", "240p"]

# ================= STATES =================
MAINTENANCE = False
CONTACT_MODE = {}

# ================= INTRO TEXT (LOCKED) =================
INTRO_TEXT = """🎬 𝗧𝗠𝗞𝗢𝗖 𝗘𝗽𝗶𝘀𝗼𝗱𝗲 𝗕𝗼𝘁

Namaste 🙏

Yeh bot specially *Taarak Mehta Ka Ooltah Chashmah* ke sabhi fans ke liye
design kiya gaya hai ❤️  
Yahan aapko TMKOC ke purane aur naye episodes
simple, fast aur ad-free tareeke se milenge.

━━━━━━━━━━━━━━━━━━
✨ Bot ke Main Features
━━━━━━━━━━━━━━━━━━
• 📺 TMKOC ke old & latest episodes  
• 🎥 Multiple video qualities  
  (240p, 360p, 540p, 720p, 1080p)  
• ⚡ Fast delivery & clean interface  
• 🚫 Koi ads, koi extra steps nahi  

━━━━━━━━━━━━━━━━━━
📌 Bot Use Karne Ka Tarika
━━━━━━━━━━━━━━━━━━
1️⃣ Sirf episode number likho  
2️⃣ Available quality select karo  
3️⃣ Episode enjoy karo 😄  

🧾 Example:
4627

━━━━━━━━━━━━━━━━━━
⚠️ Zaroori Suchna
━━━━━━━━━━━━━━━━━━
Copyright aur safety reasons ki wajah se
episodes limited time ke liye available hote hain.

👉 Episode milte hi Saved Messages me forward kar lena 📥

━━━━━━━━━━━━━━━━━━
🔗 Official Channel
━━━━━━━━━━━━━━━━━━
👉 @tmkocdirect

🙏 Dhanyavaad!
Happy Watching 😊
"""

NOT_FOUND_TEXT = (
    "❌ Episode available nahi hai 😔\n\n"
    "Agar request karni ho to /contact use karein."
)

FOUND_TEXT = (
    "🎉 Episode mil gaya 😄\n\n"
    "Niche se quality select karein 👇"
)

CONTACT_START_TEXT = (
    "📩 Contact Admin Mode ON\n\n"
    "Ab aap jo bhi message bhejenge\n"
    "wo seedha admin tak jayega."
)

EXIT_TEXT = (
    "✅ Contact mode OFF\n\n"
    "Ab aap normal tarike se bot use kar sakte ho."
)

MAINTENANCE_TEXT = (
    "🔧 Bot abhi maintenance me hai.\n\n"
    "Kripya thodi der baad try karein 🙏"
)

# ================= CUSTOM CAPTION =================
CUSTOM_CAPTION = (
    "━━━━━━━━━━━━━━━━━━\n"
    "🎬 𝗧𝗠𝗞𝗢𝗖 𝗘𝗽𝗶𝘀𝗼𝗱𝗲\n\n"
    "📺 Episode: <b>{ep}</b>\n"
    "🎥 Quality: <b>{quality}</b>\n\n"
    "🔗 Join Official Channel:\n"
    "<a href='https://t.me/tmkocdirect'>@tmkocdirect</a>\n"
    "━━━━━━━━━━━━━━━━━━"
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

# ================= FORCE SUB (LIVE CHECK) =================
async def is_verified(user_id, context):
    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    CONTACT_MODE.pop(uid, None)

    if MAINTENANCE and uid != ADMIN_ID:
        await update.message.reply_text(MAINTENANCE_TEXT)
        return

    if not await is_verified(uid, context):
        keyboard = [
            [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Tmkocc_backup")],
            [InlineKeyboardButton("✅ Verify Now", callback_data="verify")]
        ]
        await update.message.reply_text(
            "🔒 Pehle channel join karo, phir verify karo 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(INTRO_TEXT)

# ================= VERIFY =================
async def verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if await is_verified(q.from_user.id, context):
        await q.edit_message_text("✅ Verification successful 🎉")
        await context.bot.send_message(q.message.chat_id, INTRO_TEXT)
    else:
        await q.answer("❌ Pehle channel join karo", show_alert=True)

# ================= CONTACT =================
async def contact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    CONTACT_MODE[uid] = True

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Exit Contact Mode", callback_data="exit_contact")]
    ])

    await update.message.reply_text(
        CONTACT_START_TEXT,
        reply_markup=keyboard
    )

async def exit_contact_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    CONTACT_MODE.pop(q.from_user.id, None)
    await q.answer()
    await q.edit_message_text(EXIT_TEXT)

# ================= AUTO SAVE FROM SOURCE CHANNEL =================
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
            f"📩 Message from user {uid}\n\n{update.message.text}"
        )
        await update.message.reply_text("✅ Message admin ko bhej diya gaya.")
        return

    if not await is_verified(uid, context):
        await start(update, context)
        return

    ep = update.message.text.strip()
    if not ep.isdigit():
        return

    processing = await update.message.reply_text("⏳ Episode check ho raha hai...")
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
                buttons.append([
                    InlineKeyboardButton(
                        f"🎥 {q}",
                        callback_data=f"send|{ep}|{q}|{r[2]}"
                    )
                ])

    await update.message.reply_text(
        FOUND_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= SEND VIDEO =================
async def send_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, ep, quality, msg_id = q.data.split("|")
    msg_id = int(msg_id)

    sent = await context.bot.copy_message(
        chat_id=q.message.chat_id,
        from_chat_id=SOURCE_CHANNEL,
        message_id=msg_id
    )

    await context.bot.send_message(
        chat_id=q.message.chat_id,
        text=CUSTOM_CAPTION.format(ep=ep, quality=quality),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    warn = await context.bot.send_message(
        chat_id=q.message.chat_id,
        text=(
            "⚠️ Important Notice\n\n"
            "Copyright / safety reasons ki wajah se\n"
            "ye episode 2 minutes me delete ho jaayega ⏳\n\n"
            "Saved Messages me forward kar lena 📥"
        )
    )

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
    app.add_handler(CallbackQueryHandler(exit_contact_cb, pattern="^exit_contact$"))
    app.add_handler(CallbackQueryHandler(send_cb, pattern="^send"))

    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))

    print("Bot running – FINAL STABLE VERSION")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
