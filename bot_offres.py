from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import asyncio
from datetime import datetime


JOOBLE_API_KEY = "3bea11aa-ff1d-41cc-ac9d-7089e66a9d47"
TELEGRAM_BOT_TOKEN = "7560094699:AAH_6B7QAZ260iyRTAKLFF0nNOH3coe3jFE"
CHECK_INTERVAL = 2 * 60 * 60  # 2 heures en secondes


user_preferences = {}   # chat_id -> {'job': ..., 'city': ...}
sent_offers = {}       # chat_id -> liste des liens déjà envoyés

# =================== FONCTIONS ===================
def get_job_offers(keyword, location):
    """Récupère les offres depuis Jooble"""
    url = f"https://jooble.org/api/{JOOBLE_API_KEY}"
    payload = {"keywords": keyword, "location": location, "page": 1}
    response = requests.post(url, json=payload)
    jobs = response.json().get("jobs", [])

    # Trier par date décroissante (les plus récentes en premier)
    # Remplace 'date' par le champ exact renvoyé par l'API si nécessaire
    for job in jobs:
        if 'date' not in job:
            job['date'] = datetime.now().isoformat()  # si pas de date, utiliser maintenant

    jobs_sorted = sorted(jobs, key=lambda x: x['date'], reverse=True)
    return jobs_sorted

async def send_new_offers(chat_id):
    """Envoie les nouvelles offres à un utilisateur spécifique"""
    prefs = user_preferences.get(chat_id)
    if not prefs:
        return

    offers = get_job_offers(prefs['job'], prefs['city'])
    for offer in offers[:20]:
        link = offer['link']
        if link not in sent_offers.get(chat_id, []):
            message = f"💼 {offer['title']}\n🏢 {offer['company']}\n📍 {offer['location']}\n🔗 {link}"
            await bot.send_message(chat_id=chat_id, text=message)
            sent_offers.setdefault(chat_id, []).append(link)

async def periodic_check():
    """Vérifie toutes les 2h les nouvelles offres pour tous les utilisateurs"""
    while True:
        for chat_id in user_preferences.keys():
            try:
                await send_new_offers(chat_id)
            except Exception as e:
                print(f"Erreur lors de l'envoi à {chat_id}: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("Salut 👋 ! Quel métier cherches-tu ?")
    user_preferences[chat_id] = {"step": "job"}

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
        await send_new_offers(chat_id)
    else:
        await update.message.reply_text("Tape /start pour recommencer 😊")

    user_preferences[chat_id] = user


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot = app.bot

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Lancer la vérification périodique
    app.job_queue.run_repeating(lambda ctx: asyncio.create_task(periodic_check()), interval=CHECK_INTERVAL, first=10)

    print("✅ Bot démarré !")
    app.run_polling()