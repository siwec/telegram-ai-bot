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
MODEL = "qwen-turbo"

if not BOT_TOKEN or not DASHSCOPE_API_KEY:
    raise ValueError("❌ Отсутствуют BOT_TOKEN или DASHSCOPE_API_KEY в Variables на Railway!")

# === 1. СНАЧАЛА — полные тексты (для продажи) ===
DIGITAL_PRODUCTS_FULL = {
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

# === 2. ТОЛЬКО ПОСЛЕ ЭТОГО — TRIAL_OFFERS ===
TRIAL_OFFERS = {
    "@AI_Automation_Hub": {
        "title": "«Чек-лист: 10 ИИ-инструментов для бизнеса»",
        "trial": "список из 10 инструментов без описания",
        "full_desc": "полное описание каждого инструмента + ссылки + кейсы",
        "outline": (
            "1. Qwen\n"
            "2. Notion AI\n"
            "3. Zapier + ИИ\n"
            "4. Trello + Butler\n"
            "5. Canva Magic Studio\n"
            "6. Otter.ai\n"
            "7. GrammarlyGO\n"
            "8. Tome.app\n"
            "9. Bardeen\n"
            "10. Make.com\n\n"
            "💎 Полная версия — с инструкциями и примерами."
        )
    },
    "@Earn_InTelegram": {
        "title": "«Гайд: $100 через Stars за 7 дней»",
        "trial": "7 шагов без пояснений",
        "full_desc": "пошаговые инструкции, скриншоты, шаблоны",
        "outline": (
            "1. Создать бота\n"
            "2. Подключить Stars\n"
            "3. Сделать цифровой товар\n"
            "4. Написать первый пост\n"
            "5. Настроить автопостинг\n"
            "6. Добавить призыв к шеру\n"
            "7. Повторять\n\n"
            "💎 Полная версия — с примерами и шаблонами."
        )
    },
    "@CryptoAI_Guide": {
        "title": "«ТОП-5 криптоактивов на неделю»",
        "trial": "список из 5 активов",
        "full_desc": "анализ, цели, риски для каждого",
        "outline": (
            "1. BTC\n"
            "2. ETH\n"
            "3. SOL\n"
            "4. TON\n"
            "5. RNDR\n\n"
            "💎 Полная версия — с техническим и фундаментальным анализом."
        )
    },
    "@SmartHabits_AI": {
        "title": "«7-дневный челлендж продуктивности»",
        "trial": "7 заголовков дней",
        "full_desc": "пошаговые действия на каждый день",
        "outline": (
            "1. Утро без телефона\n"
            "2. 3 главные задачи\n"
            "3. Блокировка соцсетей\n"
            "4. Вечерний ревью\n"
            "5. Цифровой детокс\n"
            "6. Планирование недели\n"
            "7. Отдых без вины\n\n"
            "💎 Полная версия — с таймингом и лайфхаками."
        )
    },
    "@FinAI_Guide": {
        "title": "«Шаблон бюджета + калькулятор»",
        "trial": "структура таблицы",
        "full_desc": "готовый Google Sheets с формулами",
        "outline": (
            "1. Доходы\n"
            "2. Обязательные расходы\n"
            "3. Переменные расходы\n"
            "4. Накопления\n"
            "5. Инвестиции\n\n"
            "💎 Полная версия — с автоматическим расчётом и визуализацией."
        )
    },
    "@HealthAI_Tips": {
        "title": "«План питания от ИИ»",
        "trial": "меню на день (без описания)",
        "full_desc": "рецепты, калории, бжу, советы",
        "outline": (
            "Завтрак: овсянка + ягоды\n"
            "Обед: белок + овощи\n"
            "Ужин: лёгкий\n"
            "Перекусы: йогурт, фрукты\n"
            "Вода: 30 мл/кг\n\n"
            "💎 Полная версия — с альтернативами и сезонными продуктами."
        )
    },
    "@GrowthAI_Hacks": {
        "title": "«10 шаблонов для вирусных постов»",
        "trial": "10 заголовков шаблонов",
        "full_desc": "готовые тексты под копипаст",
        "outline": (
            "1. «Сохрани — пригодится»\n"
            "2. «3 ошибки...»\n"
            "3. «Как я заработал...»\n"
            "4. «Чек-лист...»\n"
            "5. «ТОП-5...»\n"
            "6. «Сравнение до/после»\n"
            "7. «Секрет...»\n"
            "8. «Вопрос + ответ»\n"
            "9. «Личный опыт»\n"
            "10. «Шаг за шагом»\n\n"
            "💎 Полная версия — с примерами и эмодзи."
        )
    },
    "@LearnAI_Fast": {
        "title": "«Курс: Notion за 1 день»",
        "trial": "список уроков",
        "full_desc": "скриншоты, шаблоны, ссылки",
        "outline": (
            "1. Базы и связи\n"
            "2. Шаблоны для задач\n"
            "3. Интеграция с календарём\n"
            "4. Автоматизация через кнопки\n"
            "5. Синхронизация с Telegram\n\n"
            "💎 Полная версия — с Notion-пространством по ссылке."
        )
    },
    "@MindAI_Daily": {
        "title": "«30 упражнений для снижения тревожности»",
        "trial": "30 заголовков упражнений",
        "full_desc": "пошаговые инструкции + время + эффект",
        "outline": (
            "1. Дыхание 4-7-8\n"
            "2. Заземление (5-4-3-2-1)\n"
            "3. Журнал благодарности\n"
            "4. Телесное сканирование\n"
            "5. Медитация «Тело как облако»\n"
            "... до 30\n\n"
            "💎 Полная версия — с аудио-подсказками и PDF."
        )
    },
    "@TechAI_Now": {
        "title": "«ТОП-10 гаджетов 2025»",
        "trial": "список из 10 гаджетов",
        "full_desc": "описание, цена, ссылка с кэшбэком",
        "outline": (
            "1. iPhone 16 Pro\n"
            "2. Samsung Galaxy Ring\n"
            "3. Apple Vision Pro\n"
            "4. DJI Avata 2\n"
            "5. Framework Laptop\n"
            "6. Sony WH-1000XM6\n"
            "7. Kindle Scribe\n"
            "8. DJI Mic 2\n"
            "9. Anker 737 Charger\n"
            "10. Logitech MX Master 3S\n\n"
            "💎 Полная версия — с промокодами и сравнением."
        )
    }
}

user_channels = {}
logging.basicConfig(level=logging.INFO)

# === ОБРАБОТЧИКИ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напишите /guide, чтобы получить полезный материал.")

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    referrer = None

    if chat.type == "private" and update.message.forward_from_chat:
        username = update.message.forward_from_chat.username
        if username:
            referrer = f"@{username}"

    if not referrer:
        keyboard = [[InlineKeyboardButton(ch, callback_data=f"sel_{ch}")] for ch in TRIAL_OFFERS.keys()]
        await update.message.reply_text("Выберите канал:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    user_channels[user_id] = referrer
    await send_trial_offer(update, context, referrer)

async def select_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channel = query.data.replace("sel_", "")
    user_channels[query.from_user.id] = channel
    await send_trial_offer(query, context, channel)

async def send_trial_offer(update_or_query, context, channel):
    data = TRIAL_OFFERS[channel]
    msg = (
        f"💬 Хотите получить {data['title']}?\n\n"
        f"✅ **Бесплатно**: {data['trial']}\n"
        f"💎 **Полная версия (49 Stars)**: {data['full_desc']}"
    )
    keyboard = [
        [
            InlineKeyboardButton("🔘 Бесплатно: оглавление", callback_data=f"trial_{channel}"),
            InlineKeyboardButton("💎 Полный гайд — 49 Stars", callback_data=f"full_{channel}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update_or_query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_trial_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("trial_"):
        channel = data.replace("trial_", "")
        outline = TRIAL_OFFERS[channel]["outline"]
        await query.message.reply_text(f"Вот оглавление:\n\n{outline}")
    elif data.startswith("full_"):
        channel = data.replace("full_", "")
        await send_invoice_from_callback(query, context, channel)

async def send_invoice_from_callback(query, context, channel):
    title = f"Цифровой гайд: {channel}"
    description = "Мгновенная доставка после оплаты. Сохраните в избранное!"
    payload = f"product_{channel}"
    prices = [LabeledPrice("Гайд", 49)]

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
    payload = update.message.successful_payment.invoice_payload
    channel = payload.replace("product_", "")
    if channel in DIGITAL_PRODUCTS_FULL:
        await update.message.reply_text(f"Спасибо! Вот ваш гайд:\n\n{DIGITAL_PRODUCTS_FULL[channel]}")
    else:
        await update.message.reply_text("Ошибка: товар не найден.")

# === АВТОПУБЛИКАЦИЯ ===
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
            headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "input": {"messages": [{"role": "user", "content": prompt}]}, "parameters": {"result_format": "message"}}
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
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("guide", guide))
    app.add_handler(CallbackQueryHandler(select_channel, pattern=r"^sel_"))
    app.add_handler(CallbackQueryHandler(handle_trial_choice, pattern=r"^(trial_|full_)"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    setup_scheduled_posts(app)

    print("✅ Бот запущен: кнопки + Stars + 2 поста/день")
    app.run_polling()
