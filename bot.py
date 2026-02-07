from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json, os, re, asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
DB_FILE = "episodes.json"

# Load DB
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        EPISODES = json.load(f)
else:
    EPISODES = {}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(EPISODES, f, indent=2)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("START RECEIVED")
    await update.message.reply_text("Bot alive ✅")

# ============ AUTO SAVE FROM CHANNEL ============
async def auto_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return

    msg = update.channel_post
    text = msg.caption or (msg.document.file_name if msg.document else "") or ""

    match = re.search(r"Ep\s*(\d+)", text, re.IGNORECASE)
    if not match:
        return

    ep = match.group(1)
    EPISODES[ep] = {"message_id": msg.message_id}
    save_db()

    print(f"Saved Ep{ep}")

# ================= USER SEARCH =================
async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ep = update.message.text.strip()
    if not ep.isdigit():
        return

    processing = await update.message.reply_text(
        "⏳ *Processing your request...*\n"
        "_Please wait while we find your episode_",
        parse_mode="Markdown"
    )

    await asyncio.sleep(1)

    if ep not in EPISODES:
        await processing.edit_text(
            "❌ *Episode not found*\n\n"
            "😔 Yeh episode abhi available nahi hai.\n\n"
            "📩 *Request ke liye contact karein:*\n"
            "👉 @praveen_sirvii",
            parse_mode="Markdown"
        )
        return

    await processing.edit_text(
        "✅ *Episode found!*\n🎥 Sending video...",
        parse_mode="Markdown"
    )

    await context.bot.copy_message(
        chat_id=update.message.chat_id,
        from_chat_id=SOURCE_CHANNEL,
        message_id=EPISODES[ep]["message_id"]
    )

    await processing.delete()

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))

    print("Bot running on Railway...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
