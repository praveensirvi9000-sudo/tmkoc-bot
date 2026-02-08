from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import os, asyncio, json, re, time
import gspread
from google.oauth2.service_account import Credentials

# ================= BASIC CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ Ab ye seedha Hosting ke Environment Variable se ID uthayega
ADMIN_ID = int(os.getenv("ADMIN_ID")) 

SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
FORCE_CHANNEL = "@Tmkocc_backup"
FORCE_CHANNEL_LINK = "https://t.me/Tmkocc_backup" 

AUTO_DELETE_TIME = 120  # 2 Minutes
QUALITY_ORDER = ["1080p", "720p", "540p", "360p", "240p"]
START_TIME = time.time()
BACKGROUND_TASKS = set()

# ================= STYLISH FONTS & TEXTS =================
# Maine yahan Special Unicode Fonts use kiye hain Professional Look ke liye

INTRO_TEXT = (
    "🎬 𝐓𝐌𝐊𝐎𝐂 𝐄𝐩𝐢𝐬𝐨𝐝𝐞 𝐁𝐨𝐭 🎬\n\n"
    "👋 𝐍𝐚𝐦𝐚𝐬𝐭𝐞,\n"
    "Ye bot *Taarak Mehta Ka Ooltah Chashmah* ke fans ke liye banaya gaya hai. ❤️\n\n"
    "⚠️ 𝐈𝐌𝐏𝐎𝐑𝐓𝐀𝐍𝐓 𝐍𝐎𝐓𝐈𝐂𝐄\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "📌 *Hamare paas Episode 4600 se lekar abhi tak ke (Latest) episodes available hain.*\n\n"
    "📌 _Isse pehle ke (Old) episodes aapko YouTube par aasani se mil jayenge._\n\n"
    "✨ 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬:\n"
    "📺 High Quality (1080p/HD)\n"
    "🚀 Fast & Ad-Free\n"
    "⏱️ Auto-Delete Security\n\n"
    "👇 𝐇𝐨𝐰 𝐭𝐨 𝐔𝐬𝐞:\n"
    "Bas Episode Number bhejein.\n\n"
    "📝 *Example:* `4627`\n\n"
    "_Happy Watching!_ 🍿"
)

NOT_FOUND_TEXT = (
    "❌ 𝐄𝐩𝐢𝐬𝐨𝐝𝐞 𝐍𝐨𝐭 𝐅𝐨𝐮𝐧𝐝\n\n"
    "Maaf karein, ye episode hamare database mein nahi mila. 😔\n\n"
    "🧐 𝐏𝐨𝐬𝐬𝐢𝐛𝐥𝐞 𝐑𝐞𝐚𝐬𝐨𝐧𝐬:\n"
    "• Ye episode 4600 se purana hai (YouTube check karein)\n"
    "• Episode abhi upload processing mein hai\n"
    "• Aapne galat number type kiya hai\n\n"
    "📞 𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐀𝐝𝐦𝐢𝐧:\n"
    "👉 @Admi88\_bot\n\n"
    "🤖 𝐓𝐌𝐊𝐎𝐂 𝐁𝐨𝐭"
)

AUTO_DELETE_TEXT = (
    "⚠️ 𝐀𝐔𝐓𝐎 𝐃𝐄𝐋𝐄𝐓𝐄 𝐀𝐋𝐄𝐑𝐓\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "🔒 *Copyright Protection Active*\n\n"
    "Ye Video Files aur ye Message agle\n"
    "⏳ *2 Minutes* mein delete ho jayenge.\n\n"
    "📥 *Tip:* Video ko turant apne _Saved Messages_ mein forward kar lein.\n\n"
    "❤️ 𝐓𝐡𝐚𝐧𝐤 𝐲𝐨𝐮 𝐟𝐨𝐫 𝐒𝐮𝐩𝐩𝐨𝐫𝐭"
)

# ================= GOOGLE SHEET =================
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

# ================= FORCE SUB (STRICT MODE) =================
async def check_subscription(user_id, context):
    try:
        # Har request pe live check karega
        member = await context.bot.get_chat_member(FORCE_CHANNEL, user_id)
        if member.status in ("member", "administrator", "creator"):
            return True
    except:
        pass
    return False

async def send_force_sub_message(update):
    keyboard = [
        [InlineKeyboardButton("📢 𝐉𝐨𝐢𝐧 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐍𝐨𝐰", url=FORCE_CHANNEL_LINK)],
        [InlineKeyboardButton("✅ 𝐕𝐞𝐫𝐢𝐟𝐲 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧", callback_data="check_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔒 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝\n\n"
        "Bot use karne ke liye hamara Backup Channel join karna zaroori hai.\n\n"
        "👇 *Steps to Unlock:*\n"
        "1️⃣ Upar *Join Channel* button dabayein.\n"
        "2️⃣ Join karne ke baad *Verify* button dabayein."
    )
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# ================= CALLBACK (VERIFY BUTTON) =================
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if await check_subscription(user_id, context):
        await query.answer("✅ Verified! Welcome back.")
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ *Verification Successful!*\n\nAb aap koi bhi Episode number bhejein.\nExample: `4630`",
            parse_mode="Markdown"
        )
    else:
        await query.answer("❌ Aapne abhi tak Channel Join nahi kiya!", show_alert=True)

# ================= ADMIN PANEL =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return

    uptime_sec = int(time.time() - START_TIME)
    uptime_hrs = uptime_sec // 3600
    uptime_mins = (uptime_sec % 3600) // 60
    
    try:
        total = len(sheet.col_values(1)) - 1
        db_stat = "✅ Connected"
    except:
        total = "Error"
        db_stat = "❌ Error"

    msg = (
        "🛡️ 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋 🛡️\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"🤖 *System Status:* Online\n"
        f"⏳ *Uptime:* {uptime_hrs}h {uptime_mins}m\n"
        f"📂 *Database:* {db_stat}\n"
        f"📺 *Total Episodes:* {total}\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ================= SYNCED AUTO DELETE =================
async def auto_delete(messages, delay):
    await asyncio.sleep(delay)
    for m in messages:
        try: await m.delete()
        except: pass

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update.effective_user.id, context):
        await send_force_sub_message(update)
        return
    await update.message.reply_text(INTRO_TEXT, parse_mode="Markdown")

async def auto_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post: return
    msg = update.channel_post
    text = msg.caption or ""
    
    ep_match = re.search(r"Ep\s*(\d+)", text, re.IGNORECASE)
    q_match = re.search(r"(240p|360p|540p|720p|1080p)", text, re.IGNORECASE)

    if ep_match and q_match:
        sheet.append_row([ep_match.group(1), q_match.group(1), msg.message_id])
        print(f"[AUTO SAVE] Ep {ep_match.group(1)} saved")

async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update.effective_user.id, context):
        await send_force_sub_message(update)
        return

    ep = update.message.text.strip()
    if not ep.isdigit(): return

    processing = await update.message.reply_text("🔎 𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞...")
    await asyncio.sleep(0.5)

    try: rows = sheet.get("A2:C10000")
    except: 
        try: await processing.delete()
        except: pass
        await update.message.reply_text("⚠️ Server Busy. Try again in 1 min.")
        return

    data = [r for r in rows if len(r) >= 3 and str(r[0]).strip() == ep]

    try: await processing.delete()
    except: pass

    if not data:
        await update.message.reply_text(NOT_FOUND_TEXT, parse_mode="Markdown")
        return

    await update.message.reply_text(
        f"✅ 𝐄𝐩𝐢𝐬𝐨𝐝𝐞 {ep} 𝐅𝐨𝐮𝐧𝐝!\n\n_Sending files..._",
        parse_mode="Markdown"
    )

    del_list = []
    for q in QUALITY_ORDER:
        for r in data:
            if r[1] == q:
                try:
                    m = await context.bot.copy_message(
                        chat_id=update.message.chat_id,
                        from_chat_id=SOURCE_CHANNEL,
                        message_id=int(r[2])
                    )
                    del_list.append(m)
                    await asyncio.sleep(0.4)
                except: pass

    warn = await update.message.reply_text(AUTO_DELETE_TEXT, parse_mode="Markdown")
    del_list.append(warn)

    task = asyncio.create_task(auto_delete(del_list, AUTO_DELETE_TIME))
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))
    app.add_handler(CallbackQueryHandler(verify_callback))

    print("TMKOC Bot Started (Premium UI + Sync Delete)")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
                    
