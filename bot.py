from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import os, asyncio, json, re, time, html
import gspread
from google.oauth2.service_account import Credentials

# ================= BASIC CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) 
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
GOOGLE_SERVICE_JSON = os.getenv("GOOGLE_SERVICE_JSON")

# 🔥 CUSTOM LINK (Jo Caption pe click karne par khulega)
CUSTOM_LINK = "https://t.me/+6UzDZ4URQWYzNTVl"

# Main Channel Config
FORCE_CHANNEL = "@tmkocdirect"
FORCE_CHANNEL_LINK = "https://t.me/+6UzDZ4URQWYzNTVl" 

AUTO_DELETE_TIME = 120  # 2 Minutes
QUALITY_ORDER = ["1080p", "720p", "540p", "360p", "240p"]
START_TIME = time.time()
BACKGROUND_TASKS = set()

# Maintenance & User File
MAINTENANCE_MODE = False
USERS_FILE = "users.json"

# ================= TEXTS & FONTS =================
INTRO_TEXT = (
    "🎬 𝐓𝐌𝐊𝐎𝐂 𝐄𝐩𝐢𝐬𝐨𝐝𝐞 𝐁𝐨𝐭 🎬\n\n"
    "👋 𝐍𝐚𝐦𝐚𝐬𝐭𝐞,\n"
    "Ye bot *Taarak Mehta Ka Ooltah Chashmah* ke fans ke liye banaya gaya hai. ❤️\n\n"
    "✨ 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬:\n"
    "📺 High Quality (1080p/HD)\n"
    "🚀 Fast & Ad-Free\n"
    "⏱️ Auto-Delete Security\n\n"
    "👇 𝐇𝐨𝐰 𝐭𝐨 𝐔𝐬𝐞:\n"
    "Bas Episode Number bhejein.\n\n"
    "📝 *Example:* `4627` ya `Ep 4627`\n"
    "🆕 *Latest:* /latest command use karein.\n\n"
    "_Happy Watching!_ 🍿"
)

AUTO_DELETE_TEXT = (
    "⚠️ 𝐀𝐔𝐓𝐎 𝐃𝐄𝐋𝐄𝐓𝐄 𝐀𝐋𝐄𝐑𝐓\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "🔒 *Copyright Protection Active*\n\n"
    "Ye Video Files aur ye Message agle\n"
    "⏳ *2 Minutes* mein delete ho jayenge.\n\n"
    "📥 *Tip:* Video ko turant apne _Saved Messages_ mein forward kar lein."
)

MAINTENANCE_TEXT = (
    "🛠️ 𝐔𝐧𝐝𝐞𝐫 𝐌𝐚𝐢𝐧𝐭𝐞𝐧𝐚𝐧𝐜𝐞\n\n"
    "Bot abhi maintenance mode par hai.\n"
    "Kuch hi der mein wapas online hoga. ⏳\n\n"
    "_Please wait..._"
)

# ================= DATABASE CONNECTION =================
creds = Credentials.from_service_account_info(
    json.loads(GOOGLE_SERVICE_JSON),
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
)
gc = gspread.authorize(creds)
SHEET_ID = "1cm1YSfzkJ3zVXhHpCWCxDdGPNPmhEgik09Qiw0BNLk8"
sheet = gc.open_by_key(SHEET_ID).sheet1

# Load/Save Users Logic
def load_users():
    if not os.path.exists(USERS_FILE): return set()
    with open(USERS_FILE, "r") as f:
        try: return set(json.load(f))
        except: return set()

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(USERS_FILE, "w") as f: json.dump(list(users), f)

# ================= HELPER FUNCTIONS =================
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, user_id)
        if member.status in ("member", "administrator", "creator"): return True
    except: pass
    return False

async def send_force_sub_message(update):
    keyboard = [[InlineKeyboardButton("📢 𝐉𝐨𝐢𝐧 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐍𝐨𝐰", url=FORCE_CHANNEL_LINK)], [InlineKeyboardButton("✅ 𝐕𝐞𝐫𝐢𝐟𝐲 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧", callback_data="check_sub")]]
    text = "🔒 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝\n\nBot use karne ke liye hamara Main Channel join karna zaroori hai."
    if update.callback_query: await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def auto_delete(context, chat_id, message_ids, delay):
    await asyncio.sleep(delay)
    for msg_id in message_ids:
        try: await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except: pass

def get_file_size(msg):
    try:
        if msg.video: return msg.video.file_size / (1024 * 1024)
        elif msg.document: return msg.document.file_size / (1024 * 1024)
    except: return 0
    return 0

# ================= 🔥 CORE LOGIC (CAPTION FIXED) =================
async def send_episode_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, ep_num: int):
    message = update.message if update.message else update.callback_query.message
    chat_id = message.chat_id

    # YouTube Redirect for Old Episodes
    if ep_num < 4600:
        yt_link = f"https://www.youtube.com/results?search_query=Taarak+Mehta+Ka+Ooltah+Chashmah+Episode+{ep_num}".replace(" ", "+")
        keyboard = [[InlineKeyboardButton("📺 Watch on YouTube", url=yt_link)]]
        await message.reply_text(f"ℹ️ *Episode {ep_num} Available on YouTube*\n\nClick button below to watch 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Database Search
    processing = await message.reply_text("🔎 𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞...")
    await asyncio.sleep(0.5)

    try: rows = sheet.get("A2:C10000")
    except: 
        try: await processing.delete()
        except: pass
        await message.reply_text("⚠️ Server Busy. Try again later.")
        return

    data = [r for r in rows if len(r) >= 3 and str(r[0]).strip() == str(ep_num)]
    try: await processing.delete()
    except: pass

    if not data:
        keyboard = [[InlineKeyboardButton("📤 Request This Episode", callback_data=f"req_{ep_num}")]]
        await message.reply_text(f"❌ *Episode {ep_num} Not Found*\n\nAgar ye naya episode hai, to Request karein 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await message.reply_text(f"✅ 𝐄𝐩𝐢𝐬𝐨𝐝𝐞 {ep_num} 𝐅𝐨𝐮𝐧𝐝!\n\n_Sending files..._", parse_mode="Markdown")

    msg_ids_to_delete = []

    for q in QUALITY_ORDER:
        for r in data:
            if r[1] == q:
                try:
                    # 1. COPY MESSAGE
                    m = await context.bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=SOURCE_CHANNEL,
                        message_id=int(r[2])
                    )
                    
                    # 2. GET DETAILS
                    file_size = get_file_size(m)
                    
                    # 3. CLEAN CAPTION (HTML SAFE)
                    original_cap = m.caption if m.caption else f"TMKOC Episode {ep_num} {q}"
                    # 🔥 Important: html.escape use kiya hai taaki filename HTML break na kare
                    clean_cap = html.escape(original_cap)
                    
                    # 4. CREATE NEW CAPTION
                    new_caption = (
                        f"<b><a href='{CUSTOM_LINK}'>{clean_cap}</a></b>\n"
                        f"📁 Size: {file_size:.1f} MB\n\n"
                        f"🤖 @AutoMovie_Filter_Bot | 📢 @tmkocdirect"
                    )

                    # 5. EDIT CAPTION
                    await context.bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=m.message_id,
                        caption=new_caption,
                        parse_mode="HTML"
                    )

                    msg_ids_to_delete.append(m.message_id)
                    await asyncio.sleep(0.4)
                except Exception as e: 
                    # Error aayega to console me dikhega
                    print(f"❌ Caption Edit Error: {e}")
                    # Agar edit fail hua to message ID fir bhi delete list me daalo
                    msg_ids_to_delete.append(m.message_id)

    warn = await message.reply_text(AUTO_DELETE_TEXT, parse_mode="Markdown")
    msg_ids_to_delete.append(warn.message_id)

    task = asyncio.create_task(auto_delete(context, chat_id, msg_ids_to_delete, AUTO_DELETE_TIME))
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    if MAINTENANCE_MODE and user_id != ADMIN_ID:
        await update.message.reply_text(MAINTENANCE_TEXT, parse_mode="Markdown")
        return
    if not await check_subscription(user_id, context):
        await send_force_sub_message(update)
        return
    await update.message.reply_text(INTRO_TEXT, parse_mode="Markdown")

async def latest_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if MAINTENANCE_MODE and user_id != ADMIN_ID:
        await update.message.reply_text(MAINTENANCE_TEXT, parse_mode="Markdown")
        return
    if not await check_subscription(user_id, context):
        await send_force_sub_message(update)
        return

    processing = await update.message.reply_text("🔄 Fetching Latest Episodes...")
    try:
        all_eps = sheet.col_values(1)
        if len(all_eps) > 1:
            all_eps = all_eps[1:]
            seen = set()
            unique_eps = []
            for ep in reversed(all_eps):
                if ep not in seen and ep.isdigit():
                    seen.add(ep)
                    unique_eps.append(ep)
                    if len(unique_eps) >= 6: break
            
            if not unique_eps:
                await processing.edit_text("❌ No episodes found.")
                return

            keyboard = []
            row = []
            for ep in unique_eps:
                row.append(InlineKeyboardButton(f"Ep {ep}", callback_data=f"val_{ep}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row: keyboard.append(row)

            await processing.delete()
            await update.message.reply_text("🆕 *Latest Added Episodes*\n\nClick to watch directly 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else: await processing.edit_text("❌ Database Empty.")
    except Exception as e: await processing.edit_text(f"Error: {e}")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    uptime = int(time.time() - START_TIME) // 60
    total_users = len(load_users())
    try: total_files = len(sheet.col_values(1)) - 1
    except: total_files = "Error"
    maint_status = "🔴 ON" if MAINTENANCE_MODE else "🟢 OFF"
    
    msg = (
        "👮‍♂️ *Admin Control Panel*\n━━━━━━━━━━━━━━━━\n"
        f"👥 *Total Users:* {total_users}\n"
        f"📂 *Total Files:* {total_files}\n"
        f"⏳ *Uptime:* {uptime} Mins\n"
        f"🛠️ *Maintenance:* {maint_status}\n"
    )
    keyboard = [[InlineKeyboardButton(f"Toggle Maintenance {'(OFF)' if MAINTENANCE_MODE else '(ON)'}", callback_data="toggle_maint")]]
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# 🔥 Reply Fix: Markdown hataya taaki error na aaye
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Format: `/reply UserID Message`")
            return
        target = int(args[0])
        msg = " ".join(args[1:])
        await context.bot.send_message(chat_id=target, text=f"📩 Admin Message:\n\n{msg}")
        await update.message.reply_text(f"✅ Sent to `{target}`")
    except Exception as e: await update.message.reply_text(f"Error: {e}")

async def auto_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post: return
    msg = update.channel_post
    text = msg.caption or ""
    ep_match = re.search(r"Ep\s*(\d+)", text, re.IGNORECASE)
    q_match = re.search(r"(240p|360p|540p|720p|1080p)", text, re.IGNORECASE)
    if ep_match and q_match:
        sheet.append_row([ep_match.group(1), q_match.group(1), msg.message_id])
        print(f"[AUTO SAVE] Ep {ep_match.group(1)} saved")

async def get_episode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    if MAINTENANCE_MODE and user_id != ADMIN_ID:
        await update.message.reply_text(MAINTENANCE_TEXT, parse_mode="Markdown")
        return
    if not await check_subscription(user_id, context):
        await send_force_sub_message(update)
        return

    text = update.message.text.strip()
    match = re.search(r"(\d+)", text)
    if not match: return
    await send_episode_logic(update, context, int(match.group(1)))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MAINTENANCE_MODE
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    if data == "toggle_maint":
        if user_id == ADMIN_ID:
            MAINTENANCE_MODE = not MAINTENANCE_MODE
            await query.answer(f"Maintenance: {'ON' if MAINTENANCE_MODE else 'OFF'}")
            await admin_panel(update, context)
        else: await query.answer("Only Admin!", show_alert=True)
    elif data.startswith("val_"):
        await query.answer()
        await send_episode_logic(update, context, int(data.split("_")[1]))
    elif data == "check_sub":
        if await check_subscription(user_id, context):
            await query.answer("✅ Verified!")
            await query.message.delete()
            await context.bot.send_message(chat_id=user_id, text="✅ *Verified!* Send Episode Number.", parse_mode="Markdown")
        else: await query.answer("❌ Join Channel First!", show_alert=True)
    elif data.startswith("req_"):
        ep_num = data.split("_")[1]
        try:
            await query.edit_message_text(f"✅ 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐒𝐞𝐧𝐭 for Ep {ep_num}!")
            admin_msg = f"📨 *Request*\n👤 {query.from_user.first_name}\n🆔 `{user_id}`\n📺 Ep: *{ep_num}*\n`/reply {user_id} msg`"
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
        except: await query.answer("Error")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("latest", latest_episodes))
    app.add_handler(CommandHandler("reply", reply_to_user))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("TMKOC Bot Running... (ALL FEATURES ACTIVE)")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
            
