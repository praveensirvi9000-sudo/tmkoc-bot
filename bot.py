from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json, os, re, asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
DB_FILE = "episodes.json"

# ================= LOAD DB =================
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
    await update.message.reply_text(
        "🎬 Welcome to TMKOC Episode Bot! 🎬\n\n"
        "🙏 Namaste!\n\n"
        "Yeh bot Taarak Mehta Ka Ooltah Chashmah ke fans ke liye banaya gaya hai ❤️\n\n"
        "📺 Bot ka use:\n"
        "- Sirf episode number bhejo\n"
        "- Episode ki saari available qualities automatically mil jaayengi\n\n"
        "✨ Example:\n"
        "4627\n\n"
        "📩 Request ke liye:\n"
        "@praveen_sirvii"
    )

# ================= AUTO SAVE FROM CHANNEL =================
async def auto_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return

    msg = update.channel_post
    text = msg.caption or (msg.document.file_name if msg.document else "") or ""

    # episode number
    ep_match = re.search(r"Ep\s*(\d+)", text, re.IGNORECASE)
    if not ep_match:
        return
    ep = ep_match.group(1)

    # quality detect
    q_match = re.search(r"(480p|720p|1080p)", text, re.IGNORECASE)
    quality = q_match.group(1).lower() if q_match else "unknown"

    if ep not in EPISODES:
        EPISODES[ep] = {}

    EPISODES[ep][quality] = msg.message_id
    save_db()

    print(f"Saved Ep{ep} [{quality}]")

# ================= USER SEARCH =================
async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ep = update.message.text.strip()

    if not ep.isdigit():
        return

    if ep not in EPISODES:
        await update.message.reply_text(
            "❌ Episode not available\n\n"
            "📩 Request ke liye contact karein:\n"
            "@praveen_sirvii"
        )
        return

    await update.message.reply_text(
        f"🎬 Episode {ep} found\n"
        "📤 Sending all available qualities..."
    )

    # send all qualities
    for quality in sorted(EPISODES[ep].keys(), reverse=True):
        await context.bot.copy_message(
            chat_id=update.message.chat_id,
            from_chat_id=SOURCE_CHANNEL,
            message_id=EPISODES[ep][quality]
        )
        await asyncio.sleep(0.5)  # small delay (safe)

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
