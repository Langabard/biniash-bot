import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = None  # будет установлен при первом /start от админа

# Состояния диалога
SERVICE, COMPANY_NAME, NICHE, EXAMPLES, BUDGET, CONTACT = range(6)

SERVICES = [
    "1️⃣ Бренд с нуля",
    "2️⃣ Обновить существующий бренд",
    "3️⃣ Дизайн упаковки и товаров",
    "4️⃣ Узнать цены",
]

BUDGETS = [
    "💰 До $500",
    "💰 $500 - $1,500",
    "💰 $1,500 - $5,000",
    "💰 От $5,000",
    "🤔 Пока не знаю",
]

# Хранилище данных клиентов
leads = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    leads[user_id] = {}

    keyboard = [[s] for s in SERVICES]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "✦ Говорят, первое впечатление нельзя произвести дважды.\n"
        "Мы в Biniash Studio делаем так, чтобы ваш бренд производил его правильно — с первого раза.\n\n"
        "Расскажите о вашем проекте.\n\n"
        "Что вам нужно?",
        reply_markup=reply_markup,
    )
    return SERVICE


async def service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    leads[user_id]["service"] = update.message.text

    await update.message.reply_text(
        "Отличный выбор. 👌\n\nКак называется ваша компания или проект?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return COMPANY_NAME


async def company_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    leads[user_id]["company"] = update.message.text

    await update.message.reply_text(
        f"Приятно познакомиться! ✦\n\nВ какой нише работает {update.message.text}?\n"
        "Например: технологии, ресторанный бизнес, мода, стартап, производство..."
    )
    return NICHE


async def niche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    leads[user_id]["niche"] = update.message.text

    await update.message.reply_text(
        "Понял вас. 🎯\n\nЕсть ли бренды или стили которые вам нравятся?\n"
        "Можете прислать примеры или просто описать словами.\n\n"
        "Если нет — напишите «нет» и мы предложим направление сами."
    )
    return EXAMPLES


async def examples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    leads[user_id]["examples"] = update.message.text

    keyboard = [[b] for b in BUDGETS]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Хорошо, это поможет нам точнее попасть в цель. ✦\n\nКакой бюджет вы рассматриваете?",
        reply_markup=reply_markup,
    )
    return BUDGET


async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    leads[user_id]["budget"] = update.message.text

    await update.message.reply_text(
        "Почти готово! Осталось последнее. 📋\n\n"
        "Как с вами связаться?\nНапишите ваше имя и удобный способ связи "
        "(Telegram username, email или телефон).",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CONTACT


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    leads[user_id]["contact"] = update.message.text
    leads[user_id]["username"] = f"@{update.effective_user.username}" if update.effective_user.username else "нет username"

    data = leads[user_id]

    # Сообщение клиенту
    await update.message.reply_text(
        "✦ Благодарим за доверие к Biniash Studio.\n\n"
        "Мы получили всю информацию и свяжемся с вами в ближайшее время.\n\n"
        "Ждите — будет интересно. 🖤"
    )

    # Уведомление администратору
    admin_message = (
        "🔔 НОВЫЙ ЛИД — Biniash Studio\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Telegram: {data.get('username')}\n"
        f"🏢 Компания: {data.get('company')}\n"
        f"🎯 Услуга: {data.get('service')}\n"
        f"🏭 Ниша: {data.get('niche')}\n"
        f"💡 Примеры: {data.get('examples')}\n"
        f"💰 Бюджет: {data.get('budget')}\n"
        f"📞 Контакт: {data.get('contact')}\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    # Отправляем уведомление всем админам
    for admin_id in context.bot_data.get("admins", []):
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_message)
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")

    leads.pop(user_id, None)
    return ConversationHandler.END


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /admin — регистрирует тебя как администратора для получения уведомлений"""
    user_id = update.effective_user.id
    if "admins" not in context.bot_data:
        context.bot_data["admins"] = []
    if user_id not in context.bot_data["admins"]:
        context.bot_data["admins"].append(user_id)
        await update.message.reply_text(
            "✅ Вы зарегистрированы как администратор.\n"
            "Теперь вы будете получать уведомления о новых клиентах."
        )
    else:
        await update.message.reply_text("Вы уже зарегистрированы как администратор.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Диалог завершён. Если захотите вернуться — напишите /start 🖤",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, service)],
            COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name)],
            NICHE: [MessageHandler(filters.TEXT & ~filters.COMMAND, niche)],
            EXAMPLES: [MessageHandler(filters.TEXT & ~filters.COMMAND, examples)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(conv_handler)

    logger.info("Biniash Studio Bot запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
