import os
import logging
import requests
import pytz
import uuid
from datetime import time, datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, MessageHandler, ContextTypes, filters
)

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL = "qwen-turbo"
MAX_FREE_TRIALS = 2

if not BOT_TOKEN or not DASHSCOPE_API_KEY:
    raise ValueError("❌ Отсутствуют BOT_TOKEN или DASHSCOPE_API_KEY в Variables на Railway!")

# === ХРАНИЛИЩА ===
free_trials_count = {}
purchases = {}
referrals = {}
user_ref_by = {}
user_channels = {}

def get_ref_code(user_id: int) -> str:
    if user_id not in referrals:
        referrals[user_id] = str(uuid.uuid4())[:8]
    return referrals[user_id]

# === КАНАЛЫ ===
CHANNEL_DISPLAY_NAMES = {
    "AI_Automation_Hub": "@AI_Automation_Hub",
    "Earn_InTelegram": "@Earn_InTelegram",
    "CryptoAI_Guide": "@CryptoAI_Guide",
    "SmartHabits_AI": "@SmartHabits_AI",
    "FinAI_Guide": "@FinAI_Guide",
    "HealthAI_Tips": "@HealthAI_Tips",
    "GrowthAI_Hacks": "@GrowthAI_Hacks",
    "LearnAI_Fast": "@LearnAI_Fast",
    "MindAI_Daily": "@MindAI_Daily",
    "TechAI_Now": "@TechAI_Now"
}

def get_channel_key(display_name: str) -> str:
    reverse_map = {v: k for k, v in CHANNEL_DISPLAY_NAMES.items()}
    return reverse_map.get(display_name, "AI_Automation_Hub")

# === КОНТЕНТ ===
TRIAL_OFFERS = {
    "AI_Automation_Hub": "1. Qwen\n2. Notion AI\n3. Zapier + ИИ\n4. Trello + Butler\n5. Canva Magic Studio\n6. Otter.ai\n7. GrammarlyGO\n8. Tome.app\n9. Bardeen\n10. Make.com\n\n💎 Полная версия — с инструкциями.",
    "Earn_InTelegram": "1. Создать бота\n2. Подключить Stars\n3. Сделать цифровой товар\n4. Написать пост\n5. Настроить автопостинг\n6. Добавить призыв к шеру\n7. Повторять\n\n💎 Полная версия — с шаблонами.",
    "CryptoAI_Guide": "1. BTC\n2. ETH\n3. SOL\n4. TON\n5. RNDR\n\n💎 Полная версия — с анализом.",
    "SmartHabits_AI": "1. Утро без телефона\n2. 3 главные задачи\n3. Блокировка соцсетей\n4. Вечерний ревью\n5. Цифровой детокс\n6. Планирование недели\n7. Отдых без вины\n\n💎 Полная версия — с таймингом.",
    "FinAI_Guide": "1. Доходы\n2. Расходы\n3. Накопления\n4. Инвестиции\n5. Защита\n\n💎 Полная версия — с таблицей.",
    "HealthAI_Tips": "Завтрак: овсянка + ягоды\nОбед: белок + овощи\nУжин: лёгкий\nПерекусы: йогурт, фрукты\nВода: 30 мл/кг\n\n💎 Полная версия — с БЖУ.",
    "GrowthAI_Hacks": "1. «Сохрани»\n2. «3 ошибки»\n3. «Как я заработал»\n4. «Чек-лист»\n5. «ТОП-5»\n6. «Сравнение»\n7. «Секрет»\n8. «Вопрос»\n9. «Опыт»\n10. «Шаг за шагом»\n\n💎 Полная версия — с эмодзи.",
    "LearnAI_Fast": "1. Базы\n2. Шаблоны\n3. Календарь\n4. Кнопки\n5. Telegram\n\n💎 Полная версия — с Notion.",
    "MindAI_Daily": "1. Дыхание 4-7-8\n2. Заземление\n3. Благодарность\n4. Сканирование\n5. Медитация\n... до 30\n\n💎 Полная версия — с PDF.",
    "TechAI_Now": "1. iPhone 16 Pro\n2. Galaxy Ring\n3. Vision Pro\n4. DJI Avata 2\n5. Framework Laptop\n6. WH-1000XM6\n7. Kindle Scribe\n8. DJI Mic 2\n9. Anker Charger\n10. MX Master 3S\n\n💎 Полная версия — с промокодами."
}

DIGITAL_PRODUCTS_49 = {
    "HealthAI_Tips": "Подробный план питания:\n\n- Завтрак: овсянка (40г) + ягоды (100г) + миндаль (10г)\n  БЖУ: 320 ккал | Б: 10г | Ж: 12г | У: 45г\n- Обед: курица (150г) + брокколи (200г) + киноа (50г)\n  БЖУ: 450 ккал | Б: 35г | Ж: 15г | У: 40г\n- Ужин: рыба (120г) + салат (150г)\n  БЖУ: 280 ккал | Б: 25г | Ж: 10г | У: 20г",
    "Earn_InTelegram": "Подробный гайд:\n\nШаг 1: Создайте бота через @BotFather\nШаг 2: Включите Telegram Stars\nШаг 3: Создайте PDF с чек-листом\nШаг 4: Напишите пост с призывом\nШаг 5: Настройте автопостинг через Railway\nШаг 6: Добавьте «Перешли другу»\nШаг 7: Повторяйте ежедневно",
}

DIGITAL_PRODUCTS_FULL = {
    "AI_Automation_Hub": "Чек-лист: 10 ИИ-инструментов\n\n1. Qwen — генерация текстов\n...\n10. Make.com — сценарии автоматизации\n\n📎 Notion-шаблон: https://notion.so/ai-automation-hub",
    "Earn_InTelegram": "Гайд: $100 через Stars за 7 дней\n\nШаг 1: Бот через @BotFather\n...\nШаг 7: Повторяйте\n\n📥 В комплекте: шаблоны постов + Notion-трекер: https://notion.so/earn-intelegram",
    "HealthAI_Tips": "ПОЛНЫЙ ПЛАН ПИТАНИЯ:\n\n✅ Меню с БЖУ\n✅ Советы по замене\n✅ Сезонные альтернативы\n✅ PDF для печати\n\n📎 Notion-шаблон: https://notion.so/health-ai-tips",
}

WEEKLY_GUIDE = {
    "title": "ТОП-5 ИИ-инструментов для студентов",
    "channel_key": "AI_Automation_Hub",
    "price": 29,
    "content": "Специальный гайд недели:\n\n1. Notion AI — конспекты\n2. Otter.ai — запись лекций\n3. Qwen — решение задач\n4. Tome.app — презентации\n5. Bardeen — автоматизация учёбы\n\nДоступен до: {end_date}\n\n📎 Notion: https://notion.so/weekly-student-ai"
}
WEEKLY_END = datetime.now(pytz.timezone("Europe/Moscow")) + timedelta(days=7)

logging.basicConfig(level=logging.INFO)

# === ОБРАБОТЧИКИ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args and context.args[0].startswith("ref"):
        ref_code = context.args[0][3:]
        user_ref_by[user_id] = ref_code
        await update.message.reply_text("🎁 Вы перешли по реферальной ссылке! Первый гайд — со скидкой 10%.")
    await update.message.reply_text("Напишите /guide или /profile")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    free_used = free_trials_count.get(user_id, 0)
    bought = purchases.get(user_id, [])
    ref_code = get_ref_code(user_id)
    ref_link = f"https://t.me/siwec_bot?start=ref{ref_code}"
    text = (
        f"📊 **Ваш профиль**\n\n"
        f"Бесплатных гайдов: {free_used}/{MAX_FREE_TRIALS}\n"
        f"Куплено гайдов: {len(bought)}\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"`{ref_link}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    referrer = None
    if chat.type == "private" and update.message.forward_from_chat:
        username = update.message.forward_from_chat.username
        if username:
            referrer = f"@{username}"
    if not referrer:
        keyboard = [[InlineKeyboardButton(name, callback_data=f"sel_{key}")] for key, name in CHANNEL_DISPLAY_NAMES.items()]
        await update.message.reply_text("Выберите канал:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    user_channels[user_id] = referrer
    await send_trial_offer(update, context, referrer)

async def select_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channel_key = query.data.replace("sel_", "")
    user_channels[query.from_user.id] = f"@{channel_key}"
    await send_trial_offer(query, context, f"@{channel_key}")

async def send_trial_offer(update_or_query, context, channel_display):
    channel_key = get_channel_key(channel_display)
    title = f"Гайд для {channel_display}"
    msg = f"💬 Хотите получить {title}?"
    keyboard = [
        [
            InlineKeyboardButton("🔘 Бесплатно", callback_data=f"trial_{channel_key}"),
            InlineKeyboardButton("💎 49 Stars", callback_data=f"full49_{channel_key}"),
            InlineKeyboardButton("🌟 100 Stars", callback_data=f"full100_{channel_key}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(msg, reply_markup=reply_markup)
    else:
        await update_or_query.message.reply_text(msg, reply_markup=reply_markup)

async def handle_trial_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if data.startswith("trial_"):
        if free_trials_count.get(user_id, 0) >= MAX_FREE_TRIALS:
            channel_key = data.replace("trial_", "")
            await query.message.reply_text(
                "Вы уже получили 2 бесплатных гайда. Хотите больше?",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💎 49 Stars", callback_data=f"full49_{channel_key}"),
                    InlineKeyboardButton("🌟 100 Stars", callback_data=f"full100_{channel_key}")
                ]])
            )
            return
        channel_key = data.replace("trial_", "")
        outline = TRIAL_OFFERS.get(channel_key, "Оглавление недоступно.")
        await query.message.reply_text(f"Вот оглавление:\n\n{outline}")
        free_trials_count[user_id] = free_trials_count.get(user_id, 0) + 1
    elif data.startswith("full49_"):
        channel_key = data.replace("full49_", "")
        await send_invoice(query, context, channel_key, 49, "подробная")
    elif data.startswith("full100_"):
        channel_key = data.replace("full100_", "")
        await send_invoice(query, context, channel_key, 100, "полная")

async def send_invoice(query, context, channel_key, price, version):
    display_name = CHANNEL_DISPLAY_NAMES[channel_key]
    description = "Подробное описание." if price == 49 else "Полная версия: советы, PDF, Notion."
    title = f"{version} версия: {display_name}"
    payload = f"product_{channel_key}_{price}"
    prices = [LabeledPrice("Гайд", price)]
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=prices
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    payload = update.message.successful_payment.invoice_payload
    parts = payload.split("_")
    if len(parts) < 3:
        await update.message.reply_text("Ошибка: неверный формат товара.")
        return
    channel_key = parts[1]
    price = int(parts[2])
    if user_id not in purchases:
        purchases[user_id] = []
    purchases[user_id].append(channel_key)
    content = ""
    if price == 29:
        content = WEEKLY_GUIDE["content"].format(end_date=WEEKLY_END.strftime("%d.%m"))
    elif price == 49:
        content = DIGITAL_PRODUCTS_49.get(channel_key, "Подробная версия недоступна.")
    else:
        content = DIGITAL_PRODUCTS_FULL.get(channel_key, "Полная версия недоступна.")
    await update.message.reply_text(f"Спасибо! Вот ваш гайд:\n\n{content}")

# === АВТОПУБЛИКАЦИЯ ===
async def publish_to_channels(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    channel_key = job_data["channel_key"]
    topic = job_data["topic"]
    channel_username = CHANNEL_DISPLAY_NAMES[channel_key]
    prompt = f"Напиши короткий пост для Telegram на тему: {topic}. Формат: заголовок, 3–5 пунктов, призыв сохранить и написать /guide. Стиль: дружелюбный."
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "input": {"messages": [{"role": "user", "content": prompt}]}, "parameters": {"result_format": "message"}}
        )
        post = response.json()["output"]["choices"][0]["message"]["content"] if response.status_code == 200 else f"⚠️ Ошибка API"
    except Exception as e:
        post = f"⚠️ Ошибка: {str(e)}"
    try:
        await context.bot.send_message(chat_id=channel_username, text=post)
        logging.info(f"✅ Пост в {channel_username}")
    except Exception as e:
        logging.error(f"❌ Ошибка в {channel_username}: {e}")

async def publish_weekly_guide(context: ContextTypes.DEFAULT_TYPE):
    post = f"🔥 **Гайд недели!**\n\n**{WEEKLY_GUIDE['title']}**\n\nТолько до {WEEKLY_END.strftime('%d.%m')} — **29 Stars** вместо 49!\n\n👉 Напишите /guide"
    for channel in CHANNEL_DISPLAY_NAMES.values():
        try:
            await context.bot.send_message(chat_id=channel, text=post, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка в {channel}: {e}")

def setup_scheduled_posts(application: Application):
    tz = pytz.timezone("Europe/Moscow")
    topics_map = {
        "AI_Automation_Hub": "автоматизация бизнеса через ИИ",
        "Earn_InTelegram": "заработок через Telegram Stars",
        "CryptoAI_Guide": "анализ крипторынка",
        "SmartHabits_AI": "привычка для продуктивности",
        "FinAI_Guide": "финансовая грамотность",
        "HealthAI_Tips": "здоровье и энергия",
        "GrowthAI_Hacks": "маркетинговый лайфхак",
        "LearnAI_Fast": "обучение за 10 минут",
        "MindAI_Daily": "психологическая практика",
        "TechAI_Now": "технологии будущего"
    }
    job_queue = application.job_queue
    for channel_key, topic in topics_map.items():
        data = {"channel_key": channel_key, "topic": topic}
        job_queue.run_daily(publish_to_channels, time(9, 0, tzinfo=tz), data=data)
        job_queue.run_daily(publish_to_channels, time(18, 0, tzinfo=tz), data=data)
    job_queue.run_daily(publish_weekly_guide, time(10, 0, tzinfo=tz), days=(0,))

# === ЗАПУСК ===
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("guide", guide))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CallbackQueryHandler(select_channel, pattern=r"^sel_"))
    app.add_handler(CallbackQueryHandler(handle_trial_choice, pattern=r"^(trial_|full49_|full100_)"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    setup_scheduled_posts(app)
    print("✅ Бот запущен")
    app.run_polling()
