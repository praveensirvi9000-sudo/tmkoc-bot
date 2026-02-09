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

# Admin ID (Jisko Request milegi)
ADMIN_ID = int(os.getenv("ADMIN_ID")) 

SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
FORCE_CHANNEL = "@Tmkocc_backup"
FORCE_CHANNEL_LINK = "https://t.me/Tmkocc_backup" 

AUTO_DELETE_TIME = 120  # 2 Minutes
QUALITY_ORDER = ["1080p", "720p", "540p", "360p", "240p"]
START_TIME = time.time()
BACKGROUND_TASKS = set()

# ================= TEXTS & FONTS =================
# Updated Intro: Removed specific 4600+ line as requested
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
    "📝 *Example:* `4627` ya `Ep 4627`\n\n"
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

# ================= FORCE SUB (STRICT) =================
async def check_subscription(user_id, context):
    try:
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
    text = "🔒 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝\n\nBot use karne ke liye hamara Backup Channel join karna zaroori hai."
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# ================= BUTTON HANDLERS =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # 1. VERIFY SUBSCRIPTION
    if data == "check_sub":
        if await check_subscription(user_id, context):
            await query.answer("✅ Verified! Welcome back.")
            await query.message.delete()
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ *Verification Successful!*\n\nAb aap koi bhi Episode number bhejein.\nExample: `4630` ya `Ep 4630`",
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ Aapne abhi tak Channel Join nahi kiya!", show_alert=True)

    # 2. REQUEST EPISODE
    elif data.startswith("req_"):
        ep_num = data.split("_")[1]
        try:
            # User Message
            await query.edit_message_text(
                f"✅ 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐒𝐞𝐧𝐭!\n\nEpisode {ep_num} ki request Admin ko bhej di gayi hai.\nJald hi upload hoga."
            )
            # Admin Notification
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📨 *New Episode Request*\n\nUser: {query.from_user.first_name} (ID: `{user_id}`)\nRequested: *Episode {ep_num}*",
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.answer("Error sending request.")

# ================= SYNCED AUTO DELETE =================
async def auto_delete(context, chat_id, message_ids, delay):
    await asyncio.sleep(delay)
    # Debug print
    print(f"[DELETE] Cleaning up {len(message_ids)} messages for {chat_id}")
    for msg_id in message_ids:
        try:
            # Using delete_message by ID is safest
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            pass

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
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        await send_force_sub_message(update)
        return

    text = update.message.text.strip()
    
    # 🔥 SMART REGEX: Handles "4625", "Ep 4625", "Episode 4625" etc.
    match = re.search(r"(\d+)", text)
    if not match:
        return # Agar koi number nahi mila to ignore karega
        
    ep_num = int(match.group(1)) # Extract the number

    # 🔥 LOGIC 1: OLD EPISODES -> YOUTUBE AUTO SEARCH
    if ep_num < 4600:
        # Create Search Query
        search_query = f"Taarak Mehta Ka Ooltah Chashmah Episode {ep_num}"
        # Convert spaces to + for URL
        encoded_query = search_query.replace(" ", "+")
        yt_link = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        keyboard = [[InlineKeyboardButton("📺 Watch on YouTube", url=yt_link)]]
        
        await update.message.reply_text(
            f"ℹ️ *Episode {ep_num} Available on YouTube*\n\n"
            "Ye purana episode hai, aap ise niche diye gaye button par click karke direct YouTube par dekh sakte hain. 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 🔥 LOGIC 2: DATABASE SEARCH (For 4600+)
    processing = await update.message.reply_text("🔎 𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞...")
    await asyncio.sleep(0.5)

    try: rows = sheet.get("A2:C10000")
    except: 
        try: await processing.delete()
        except: pass
        await update.message.reply_text("⚠️ Server Busy. Try again later.")
        return

    # Filter
    data = [r for r in rows if len(r) >= 3 and str(r[0]).strip() == str(ep_num)]

    try: await processing.delete()
    except: pass

    # 🔥 LOGIC 3: REQUEST BUTTON (If not found)
    if not data:
        keyboard = [[InlineKeyboardButton("📤 Request This Episode", callback_data=f"req_{ep_num}")]]
        await update.message.reply_text(
            f"❌ *Episode {ep_num} Not Found*\n\nAgar ye naya episode hai, to aap Request kar sakte hain 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # EPISODE FOUND - SENDING
    await update.message.reply_text(
        f"✅ 𝐄𝐩𝐢𝐬𝐨𝐝𝐞 {ep_num} 𝐅𝐨𝐮𝐧𝐝!\n\n_Sending files..._",
        parse_mode="Markdown"
    )

    msg_ids_to_delete = []

    for q in QUALITY_ORDER:
        for r in data:
            if r[1] == q:
                try:
                    m = await context.bot.copy_message(
                        chat_id=update.message.chat_id,
                        from_chat_id=SOURCE_CHANNEL,
                        message_id=int(r[2])
                    )
                    # ✅ Store only ID
                    msg_ids_to_delete.append(m.message_id) 
                    await asyncio.sleep(0.4)
                except: pass

    warn = await update.message.reply_text(AUTO_DELETE_TEXT, parse_mode="Markdown")
    msg_ids_to_delete.append(warn.message_id)

    # AUTO DELETE TASK
    task = asyncio.create_task(
        auto_delete(context, update.message.chat_id, msg_ids_to_delete, AUTO_DELETE_TIME)
    )
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("TMKOC Bot Running (Smart Input + YouTube Search)")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
