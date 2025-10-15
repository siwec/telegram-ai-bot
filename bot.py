import os
import logging
import requests
import pytz
from datetime import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, MessageHandler, ContextTypes, filters
)

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL = "qwen-turbo"  # или "qwen-max"

# Цифровые товары для каждого канала
DIGITAL_PRODUCTS = {
    "@AI_Automation_Hub": "Чек-лист: 10 ИИ-инструментов для автоматизации бизнеса\n\n1. Qwen — для генерации текстов, анализа, кода\n2. Notion AI — базы знаний и задачи\n3. Zapier + ИИ — связка сервисов без кода\n4. Trello + Butler — автопланирование задач\n5. Canva Magic Studio — дизайн за 1 клик\n6. Otter.ai — расшифровка встреч\n7. GrammarlyGO — умное письмо\n8. Tome.app — презентации от ИИ\n9. Bardeen — автоматизация браузера\n10. Make.com — сложные сценарии автоматизации\n\n💡 Сохрани — внедри за выходные!",
    "@Earn_InTelegram": "Гайд: Как заработать $100 через Telegram Stars за 7 дней\n\nШаг 1: Создай бота через @BotFather\nШаг 2: Подключи Telegram Stars (в настройках бота)\nШаг 3: Сделай цифровой товар (PDF, чек-лист, шаблон)\nШаг 4: Напиши пост: «Хочешь полную версию? Напиши /guide»\nШаг 5: Настрой автопостинг (1 пост/день)\nШаг 6: Добавь призыв: «Перешли другу — он скажет спасибо»\nШаг 7: Повторяй → доход растёт сам\n\n💰 Пример: 20 продаж по 49 Stars = $10/день",
    "@CryptoAI_Guide": "Сигналы + анализ: ТОП-5 криптоактивов на неделю\n\n1. BTC — коррекция завершена, цель $72K\n2. ETH — рост после ETF-новостей\n3. SOL — сильный on-chain рост\n4. TON — экосистема Telegram = долгосрочный рост\n5. RNDR — ИИ + GPU = тренд 2025\n\n⚠️ Не инвестируйте больше, чем готовы потерять. Анализ от ИИ.",
    "@SmartHabits_AI": "7-дневный челлендж продуктивности\n\nДень 1: Утро без телефона (30 мин)\nДень 2: 3 главные задачи — и только они\nДень 3: Блокировка соцсетей на 2 часа\nДень 4: Вечерний ревью дня\nДень 5: Цифровой детокс (2 часа)\nДень 6: Планирование недели\nДень 7: Отдых без вины\n\n✅ Результат: +2 часа в день",
    "@FinAI_Guide": "Шаблон бюджета + инвестиционный калькулятор (Google Sheets)\n\n- Доходы / Расходы / Накопления — автоматически\n- Правило 50/30/20 — встроенная визуализация\n- Инвестиции: ETF, крипта, недвижимость — прогноз роста\n- Доступ по ссылке — копируй и пользуйся\n\n🔗 Ссылка при покупке",
    "@HealthAI_Tips": "Персональный план питания от ИИ (PDF)\n\n- Завтрак: овсянка + ягоды + орехи\n- Обед: белок + овощи + сложные углеводы\n- Ужин: лёгкий, за 3 часа до сна\n- Перекусы: йогурт, фрукты, орехи\n- Вода: 30 мл на 1 кг веса\n- Без диет, без голода — только баланс",
    "@GrowthAI_Hacks": "10 шаблонов для вирусных постов\n\n1. «Сохрани — пригодится»\n2. «3 ошибки, которые все делают»\n3. «Как я заработал X за Y дней»\n4. «Чек-лист: сделай за 5 минут»\n5. «ТОП-5 инструментов»\n6. «Сравнение до/после»\n7. «Секрет, о котором молчат»\n8. «Вопрос + ответ»\n9. «Личный опыт»\n10. «Шаг за шагом»\n\n📝 Копируй → вставляй → публикуй",
    "@LearnAI_Fast": "Курс: Освой Notion за 1 день\n\nУрок 1: Базы и связи\nУрок 2: Шаблоны для задач\nУрок 3: Интеграция с календарём\nУрок 4: Автоматизация через кнопки\nУрок 5: Синхронизация с Telegram\n\n📁 Все шаблоны — в одном Notion-пространстве (ссылка при покупке)",
    "@MindAI_Daily": "30 упражнений для снижения тревожности\n\n1. Дыхание 4-7-8\n2. Заземление (5-4-3-2-1)\n3. Журнал благодарности\n4. Телесное сканирование\n5. Медитация «Тело как облако»\n... до 30\n\n🧘 Делай по 1 в день — тревога снижается за 2 недели",
    "@TechAI_Now": "ТОП-10 гаджетов 2025 с ссылками\n\n1. iPhone 16 Pro — ИИ-камера\n2. Samsung Galaxy Ring — здоровье\n3. Apple Vision Pro — продуктивность\n4. DJI Avata 2 — дроны\n5. Framework Laptop — ремонтопригодность\n6. Sony WH-1000XM6 — шумодав\n7. Kindle Scribe — чтение + заметки\n8. DJI Mic 2 — запись голоса\n9. Anker 737 Charger — зарядка на всё\n10. Logitech MX Master 3S — мышь для работы\n\n🔗 Все ссылки — проверенные, с кэшбэком"
}

# Хранилище для определения канала при /guide
user_channels = {}

logging.basicConfig(level=logging.INFO)

# === ОБРАБОТЧИКИ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши /guide, чтобы получить полезный материал.")

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat

    referrer = None
    if chat.type == "private":
        if update.message.forward_from_chat and update.message.forward_from_chat.type == "channel":
            username = update.message.forward_from_chat.username
            if username:
                referrer = f"@{username}"

    if not referrer:
        keyboard = [[InlineKeyboardButton(ch, callback_data=f"sel_{ch}")] for ch in DIGITAL_PRODUCTS.keys()]
        await update.message.reply_text("Выберите канал:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    user_channels[user_id] = referrer
    await send_invoice(update, context, referrer)

async def select_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channel = query.data.replace("sel_", "")
    user_channels[query.from_user.id] = channel
    await send_invoice(query, context, channel)

async def send_invoice(update_or_query, context, channel):
    title = f"Цифровой guide: {channel}"
    description = "Мгновенная доставка после оплаты. Сохраните в избранное!"
    payload = f"product_{channel}"
    prices = [LabeledPrice("Guide", 49)]

    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_invoice(
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Обязательно пусто для Stars
            currency="XTR",
            prices=prices
        )
    else:
        await update_or_query.message.reply_invoice(
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
    payload = update.message.successful_payment.invoice_payload
    channel = payload.replace("product_", "")
    if channel in DIGITAL_PRODUCTS:
        await update.message.reply_text(f"Спасибо! Вот ваш guide:\n\n{DIGITAL_PRODUCTS[channel]}")
    else:
        await update.message.reply_text("Ошибка: товар не найден.")

# === АВТОПУБЛИКАЦИЯ 2 РАЗА В ДЕНЬ ===
async def publish_to_channels(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    channel = job_data["channel"]
    topic = job_data["topic"]

    prompt = f"""
    Напиши короткий, полезный пост для Telegram-канала на тему: {topic}.
    Формат: 
    - Заголовок с эмодзи
    - 3–5 пунктов с конкретикой
    - В конце: 
      "👉 Сохрани — пригодится.
       👉 Перешли тому, кто хочет [выгода].
       👉 Хочешь полную версию? Напиши /guide"
    Стиль: дружелюбный, экспертный, без воды.
    """
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers={
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "input": {"messages": [{"role": "user", "content": prompt}]},
                "parameters": {"result_format": "message"}
            }
        )
        post = response.json()["output"]["choices"][0]["message"]["content"] if response.status_code == 200 else f"⚠️ Ошибка генерации: {topic}"
    except Exception as e:
        post = f"⚠️ Ошибка: {str(e)}"

    try:
        await context.bot.send_message(chat_id=channel, text=post)
        logging.info(f"✅ Пост в {channel}")
    except Exception as e:
        logging.error(f"❌ Ошибка в {channel}: {e}")

def setup_scheduled_posts(application: Application):
    tz = pytz.timezone("Europe/Moscow")
    topics_map = {
        "@AI_Automation_Hub": "автоматизация бизнеса через ИИ",
        "@Earn_InTelegram": "заработок через Telegram Stars",
        "@CryptoAI_Guide": "анализ крипторынка",
        "@SmartHabits_AI": "привычка для продуктивности",
        "@FinAI_Guide": "финансовая грамотность",
        "@HealthAI_Tips": "здоровье и энергия",
        "@GrowthAI_Hacks": "маркетинговый лайфхак",
        "@LearnAI_Fast": "обучение за 10 минут",
        "@MindAI_Daily": "психологическая практика",
        "@TechAI_Now": "технологии будущего"
    }

    job_queue = application.job_queue
    for channel, topic in topics_map.items():
        data = {"channel": channel, "topic": topic}
        job_queue.run_daily(publish_to_channels, time(9, 0, tzinfo=tz), data=data)
        job_queue.run_daily(publish_to_channels, time(18, 0, tzinfo=tz), data=data)
        logging.info(f"📅 Запланировано для {channel}")

# === ЗАПУСК ===
if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN.strip() == "":
        raise ValueError("❌ BOT_TOKEN не задан! Добавьте его в Variables на Railway.")
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY.strip() == "":
        raise ValueError("❌ DASHSCOPE_API_KEY не задан!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("guide", guide))
    app.add_handler(CallbackQueryHandler(select_channel, pattern=r"^sel_"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    setup_scheduled_posts(app)

    print("✅ Бот запущен: 2 поста/день + Stars")
    app.run_polling()
