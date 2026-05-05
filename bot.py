import logging
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

BOT_TOKEN     = "8735062712:AAF9odF1-Z8yaMJl3PWTpVyzwAm4Ak2ZgRc"
ADMIN_CHAT_ID = 471802287
KARTA         = "9860160630608836  —  BEKMUROD ALIMJONOV"

TARIFLAR = {
    "oddiy": {"nomi": "📗 Oddiy", "narx": "29 000 so'm"},
    "premium": {"nomi": "⚡ Premium", "narx": "49 000 so'm"},
}

CHEK_KUTILMOQDA = 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)

@flask_app.route("/")
def health():
    return "Bot ishlayapti!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    args = context.args
    tarif_key = args[0].lower() if args else ""

    if tarif_key not in TARIFLAR:
        await update.message.reply_text("Salom! 👋 Kitob sotib olish uchun saytdagi tugmani bosing.")
        return ConversationHandler.END

    tarif = TARIFLAR[tarif_key]
    context.user_data["tarif"] = tarif

    await update.message.reply_text(
        f"Salom! 👋\n\n"
        f"Siz tanlagan tarif: {tarif['nomi']}\n"
        f"Narxi: {tarif['narx']}\n\n"
        f"To'lov qilish uchun quyidagi karta raqamiga pul o'tkazing:\n\n"
        f"💳 <code>{KARTA}</code>\n\n"
        f"Pul o'tkazgandan so'ng chek rasmini shu yerga yuboring — "
        f"tekshirib kitobni PDF holatda yuboraman! 📚",
        parse_mode="HTML"
    )
    return CHEK_KUTILMOQDA

async def chek_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tarif = context.user_data.get("tarif", {})
    user = update.message.from_user
    user_info = f"@{user.username}" if user.username else f"ID: {user.id}"

    await update.message.reply_text(
        "✅ Chekingiz qabul qilindi!\n\n"
        "Tekshirib, kitobni tez orada yuboraman. Odatda 5-30 daqiqa ichida yetkaziladi 📚"
    )

    caption = (
        f"🛒 Yangi buyurtma!\n\n"
        f"👤 {user.full_name} ({user_info})\n"
        f"📦 Tarif: {tarif.get('nomi', '?')}\n"
        f"💰 Narx: {tarif.get('narx', '?')}\n\n"
        f"Chek yuqorida ⬆️"
    )

    try:
        if update.message.photo:
            await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=update.message.photo[-1].file_id, caption=caption)
        elif update.message.document:
            await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=update.message.document.file_id, caption=caption)
        else:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=caption + f"\n\nChek: {update.message.text}")
    except Exception as e:
        logger.error(f"Xato: {e}")

    return ConversationHandler.END

async def notogri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Iltimos, to'lov chekini rasm shaklida yuboring 📸")
    return CHEK_KUTILMOQDA

def main() -> None:
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHEK_KUTILMOQDA: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, chek_qabul),
                MessageHandler(filters.TEXT & ~filters.COMMAND, notogri),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    print("Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

