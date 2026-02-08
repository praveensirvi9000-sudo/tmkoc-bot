from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import os, asyncio, json, re

# ================= BASIC CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))

FORCE_CHANNEL = "@Tmkocc_backup"
AUTO_DELETE_TIME = 120  # seconds

QUALITY_ORDER = ["1080p", "720p", "540p", "360p", "240p"]

# ================= TEXTS =================
INTRO_TEXT = (
    "*TMKOC Episode Bot*\n\n"
    "_Namaste 🙏_\n\n"
    "Ye bot *Taarak Mehta Ka Ooltah Chashmah* ke fans ke liye "
    "professionally develop kiya gaya hai ❤️\n\n"
    "*Yahan aapko milega:*\n"
    "• TMKOC ke purane aur naye episodes\n"
    "• Sabhi available video qualities (240p se 1080p tak)\n"
    "• Simple, fast aur ad-free experience\n\n"
    "*Use ka tareeqa:*\n"
    "Bas episode number bhejo.\n\n"
    "*Example:*\n"
    "`4627`\n\n"
    "_Happy watching 😊_"
)

NOT_FOUND_TEXT = (
    "*❌ Episode Available Nahi Hai*\n\n"
    "Aapne jo episode number search kiya hai,\n"
    "wo abhi hamare database me maujood nahi hai 😔\n\n"
    "*Possible reasons:*\n"
    "• Episode upload nahi hua hai\n"
    "• Thodi der pehle hi telecast hua ho\n"
    "• Upload processing me ho\n\n"
    "*Aap kya kar sakte ho?*\n"
    "Agar aap is episode ki request karna chahte ho,\n"
    "to admin se directly contact karein 👇\n\n"
    "👉 @Admi88_bot\n\n"
    "_Dhanyavaad 🙏_\n"
    "*TMKOC Episode Bot*"
)

AUTO_DELETE_TEXT = (
    "*⚠️ Important Notice*\n\n"
    "Copyright aur safety reasons ki wajah se\n"
    "ye episode *2 minutes* ke andar automatically delete ho jaayega.\n\n"
    "📥 Please is video ko abhi apne _Saved Messages_ me "
    "forward kar lo.\n\n"
    "_Support ke liye shukriya ❤️_"
)

# ================= GOOGLE SHEET =================
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1cm1YSfzkJ3zVXhHpCWCxDdGPNPmhEgik09Qiw0BNLk8"
SERVICE_JSON = os.getenv("GOOGLE_SERVICE_JSON")

creds = Credentials.from_service_account_info(
    json.loads(SERVICE_JSON),
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ],
)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

# ================= FORCE SUB (FIRST TIME ONLY) =================
VERIFIED_USERS = set()

async def check_force_sub(user_id, context):
    if user_id in VERIFIED_USERS:
        return True
    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, user_id)
        if member.status in ("member", "administrator", "creator"):
            VERIFIED_USERS.add(user_id)
            return True
    except:
        pass
    return False

async def force_sub_message(update):
    await update.message.reply_text(
        "🔒 Bot use karne ke liye pehle channel join karna zaroori hai.\n\n"
        "Channel join karne ke baad fir se /start bhejein 👇\n\n"
        "@Tmkocc_backup"
    )

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_force_sub(update.effective_user.id, context):
        await force_sub_message(update)
        return
    await update.message.reply_text(INTRO_TEXT, parse_mode="Markdown")

# ================= AUTO SAVE FROM SOURCE CHANNEL =================
async def auto_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return

    msg = update.channel_post
    text = msg.caption or (msg.document.file_name if msg.document else "") or ""

    ep_match = re.search(r"Ep\s*(\d+)", text, re.IGNORECASE)
    q_match = re.search(r"(240p|360p|540p|720p|1080p)", text, re.IGNORECASE)

    if not ep_match or not q_match:
        return

    ep = ep_match.group(1)
    quality = q_match.group(1)
    msg_id = msg.message_id

    sheet.append_row([ep, quality, msg_id])
    print(f"[AUTO SAVE] Ep{ep} {quality} saved")

# ================= EPISODE SEARCH =================
async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_force_sub(update.effective_user.id, context):
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
        await update.message.reply_text(NOT_FOUND_TEXT, parse_mode="Markdown")
        return

    await update.message.reply_text(
        f"*Episode {ep} mil gaya 🎉*\n\n"
        "_Sabhi available qualities bheji ja rahi hain…_",
        parse_mode="Markdown"
    )

    sent_msgs = []

    for q in QUALITY_ORDER:
        for r in data:
            if r[1] == q:
                m = await context.bot.copy_message(
                    chat_id=update.message.chat_id,
                    from_chat_id=SOURCE_CHANNEL,
                    message_id=int(r[2])
                )
                sent_msgs.append(m)
                await asyncio.sleep(0.5)

    warn = await update.message.reply_text(
        AUTO_DELETE_TEXT,
        parse_mode="Markdown"
    )

    await asyncio.sleep(AUTO_DELETE_TIME)
    try:
        for m in sent_msgs:
            await m.delete()
        await warn.delete()
    except:
        pass

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))

    print("TMKOC Bot running (AUTO SAVE + NOT FOUND FIXED)")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
