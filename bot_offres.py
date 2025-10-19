from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests

JOOBLE_API_KEY = "3bea11aa-ff1d-41cc-ac9d-7089e66a9d47"
TELEGRAM_BOT_TOKEN = "7560094699:AAH50K28m9w9jg_MVbdj8LJf9xIfnuxT_E8"

user_preferences = {}

def get_job_offers(keyword, location):
    url = f"https://jooble.org/api/{JOOBLE_API_KEY}"
    payload = {"keywords": keyword, "location": location, "page": 1}
    response = requests.post(url, json=payload)
    return response.json().get("jobs", [])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut 👋 ! Quel métier cherches-tu ?")
    user_preferences[update.effective_chat.id] = {"step": "job"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    user = user_preferences.get(chat_id, {})
    step = user.get("step")

    if step == "job":
        user["job"] = text
        user["step"] = "city"
        await update.message.reply_text("Dans quelle ville ?")
    elif step == "city":
        user["city"] = text
        user["step"] = "done"
        await update.message.reply_text(f"Recherche d’offres pour {user['job']} à {user['city']}…")
        offers = get_job_offers(user["job"], user["city"])
        if offers:
            for offer in offers[:10]:
                message = f"💼 {offer['title']}\n🏢 {offer['company']}\n📍 {offer['location']}\n🔗 {offer['link']}"
                await update.message.reply_text(message)
        else:
            await update.message.reply_text("Aucune offre trouvée 😕")
    else:
        await update.message.reply_text("Tape /start pour recommencer 😊")

    user_preferences[chat_id] = user

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot démarré !")
    app.run_polling()