from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json, os, re, asyncio

BOT_TOKEN = os.getenv("8413029258:AAHAT_Vb4MHYIxW_J1QxNNnJYD-kU978Rss")   # Railway ENV use karega
SOURCE_CHANNEL = int(os.getenv("-1003735167884"))
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome to TMKOC Episode Bot!\n\n"
        "🧾 Episode number bhejo\n"
        "✨ Example: 4627"
    )

# AUTO SAVE FROM CHANNEL
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

# USER SEARCH
async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ep = update.message.text.strip()
    if not ep.isdigit():
        return

    processing = await update.message.reply_text("⏳ Processing...")
    await asyncio.sleep(1)

    if ep not in EPISODES:
        await processing.edit_text(
            "❌ Episode not available\n📩 Contact: @praveen_sirvii"
        )
        return

    await context.bot.copy_message(
        chat_id=update.message.chat_id,
        from_chat_id=SOURCE_CHANNEL,
        message_id=EPISODES[ep]["message_id"]
    )
    await processing.delete()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_save))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode))

    print("Bot running on Railway...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()