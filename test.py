#    & "c:/Users/Пользователь/glamcoding/.venv/Scripts/python.exe" "c:/Users/Пользователь/glamcoding/meow.py"


import logging
import openai
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, LabeledPrice, ShippingOption
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import DEEPSEEK_API_KEY

# Инициализация клиента DeepSeek
from openai import OpenAI
client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key=DEEPSEEK_API_KEY,
)

# Словарь для хранения прогресса пользователей
user_progress = {}

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("app.log"),  # Логи записываются в файл app.log
        logging.StreamHandler()         # Логи выводятся в консоль
    ]
)
logger = logging.getLogger(__name__)

# Функция для создания клавиатуры
def get_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton("Получить новый кейс", callback_data="get_case")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reply_keyboard():
    keyboard = [["Показать прогресс", "Оплатить доступ", "Тарифы"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_progress[user_id] = {"cases_solved": 0, "last_case": None}

    logger.info("Отправка приветственного сообщения с выпадающим меню.")
    await update.message.reply_text(
        "Привет, я BTrainer. Я помогаю КПТ-психотерапевтам улучшать свои профессиональные навыки. "
        "Чтобы узнать стоимость подписки, нажми на кнопку Тарифы или отправь команду /tariffs",
        reply_markup=get_reply_keyboard()
    )

# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logger.info(f"Нажата кнопка: {query.data}")
    await query.answer()
    if query.data == "get_case":
        await send_case_common(update, context)

# Функция для генерации терапевтического кейса
def generate_case():
    try:
        # Читаем содержимое файла
        file_path = r"E:\Пользователь\Documents\База знаний\Статьи.txt"
        logger.info(f"Попытка открыть файл: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            book_content = file.read()
        logger.info(f"Файл успешно прочитан, длина содержимого: {len(book_content)} символов")

        book_content = book_content[:40000]
        logger.info(f"Сокращённое содержимое: {len(book_content)} символов")

        # Проверяем, не пустой ли файл
        if not book_content.strip():
            logger.error("Файл пустой")
            return "Ошибка: файл с книгой пустой."

        prompt = (
            "Ты — помощник для студентов-психологов, обучающихся когнитивно-поведенческой терапии. "
            "Ты отлично владеешь знаниями об общей психологии, этических принципах психолога, теоретическими и практическими знаниями о когнитивно-поведенческой терапии."
            "Сгенерируй короткий терапевтический кейс для практики и ожидай решения пользователя. Кейс должен включать только название и описание кейса без целей терапии и других подробностей."
            "Кейс должен быть основан на принципах КПТ и учитывать типичные проблемы, встречающиеся на практике психолога. "
            "Пример содержания для вдохновения: " + book_content + " "
            "Не используй форматирование, HTML-теги или скобки (**, [], и т.д.)."
        )
        logger.info(f"Длина промпта: {len(prompt)} символов")

        # Отправляем запрос к DeepSeek
        logger.info("Отправка запроса к DeepSeek API")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Получить кейс"}
            ],
            stream=False
        )
        logger.info("Запрос успешно отправлен, обработка ответа")

        # Логируем полный ответ для отладки
        logger.debug(f"Полный ответ от API: {response}")

        if response and hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            cleaned_content = re.sub(r'<.*?>', '', content).strip()
            logger.info(f"Кейс успешно сгенерирован: {cleaned_content[:100]}...")
            return cleaned_content
        else:
            logger.error("API вернул пустой или некорректный ответ")
            return "Не удалось сгенерировать кейс."
    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден.")
        return "Ошибка: файл с книгой не найден."
    except Exception as e:
        logger.error(f"Ошибка при генерации кейса: {str(e)}")
        return f"Произошла ошибка при генерации кейса: {str(e)}"

# Общая функция для генерации и отправки кейса
async def send_case_common(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Получен user_id: {user_id}")
    
    # Инициализация данных пользователя, если их нет
    if user_id not in user_progress:
        user_progress[user_id] = {"cases_solved": 0, "last_case": None}
        logger.info(f"Инициализированы данные для пользователя {user_id}")
    
    ''' Показываем анимацию загрузки
    loading_message = await show_loading(update, context, duration=2)
    '''
    # Генерируем кейс
    case = generate_case()
    user_progress[user_id]["last_case"] = case
    
    # Отправляем кейс пользователю
    logger.info(f"Отправка кейса пользователю {user_id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Ваш новый терапевтический кейс:\n\n{case}\n\nВведите ваше решение.",
        reply_markup=get_inline_keyboard()
    )

# Команда /case для получения нового кейса
async def get_case(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_case_common(update, context)

# Обработчик нажатия кнопки "Получить новый кейс"
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logger.info(f"Нажата кнопка: {query.data}")
    await query.answer()
    if query.data == "get_case":
        await send_case_common(update, context)

''' Функция для показа анимации загрузки
async def show_loading(update: Update, context: ContextTypes.DEFAULT_TYPE, duration=2):
    """
    Показывает анимацию загрузки перед отправкой кейса.
    duration — время в секундах для имитации загрузки.
    """
    chat_id = update.effective_chat.id
    message = await context.bot.send_message(chat_id=chat_id, text="Загрузка кейса.")
    for i in range(3):
        await asyncio.sleep(duration / 3)  # Делим время на 3 шага
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message.message_id,
            text=f"Загрузка кейса{'.' * (i + 1)}"
        )
    return message  # Возвращаем объект сообщения для дальнейшего редактирования
'''
# Анализ решения с помощью DeepSeek
def analyze_solution(case, solution):
    try:
        prompt = (
            "Проанализируй решение, напиши его плюсы и минусы и дай рекомендации. Не используй форматирование и скобки (**, [], и т.д.)"
        )
        # Отправляем запрос к DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Решение кейса"}
            ],
            stream=False
        )

        if response and hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            cleaned_content = re.sub(r'<.*?>', '', content).strip()
            logger.info(f"Анализ решения успешно выполнен: {cleaned_content[:100]}...")
            return cleaned_content
        else:
            logger.error("API вернул пустой или некорректный ответ при анализе решения")
            return "Не удалось проанализировать решение."
    except Exception as e:
        logger.error(f"Ошибка при анализе решения: {e}")
        return "Произошла ошибка при анализе решения."


# Обработка решения пользователя
async def handle_solution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Игнорируем сообщения, которые являются кнопками
    if user_message in ["Показать прогресс", "Оплатить доступ", "Тарифы"]:
        logger.info(f"Сообщение '{user_message}' игнорируется в handle_solution")
        return

    user_id = update.effective_user.id
    user_solution = user_message
    last_case = user_progress.get(user_id, {}).get("last_case")

    if not last_case:
        logger.warning(f"Пользователь {user_id} попытался отправить решение без активного кейса")
        await update.message.reply_text(
            "Сначала получите кейс с помощью команды /case.",
            reply_markup=get_reply_keyboard()
        )
        return

    analysis = analyze_solution(last_case, user_solution)
    user_progress[user_id]["cases_solved"] += 1

 # Заменяем сообщение загрузки на результат анализа
    await update.message.reply_text(
        f"Анализ вашего решения:\n\n{analysis}",
        reply_markup=get_inline_keyboard()
    )

# Общая функция для вывода тарифов
async def show_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Получен user_id: {user_id}")
    tariffs_info = (
        "Наши тарифы:\n"
        "1. Simple — 850 руб/мес\n"
        "   - около 300 кейсов в месяц\n"
        "2. Profi — скоро появится\n"
        "Для оплаты нажми на кнопку Оплатить доступ или отправь команду /pay"
    )
    logger.info(f"Отправка анализа решения пользователю {user_id}")
    await update.message.reply_text(
        tariffs_info,
        reply_markup=get_reply_keyboard()
    )

# Команда /tariffs
async def tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_tariffs(update, context)

# Обработка кнопки "Тарифы"
async def handle_tariffs_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_tariffs(update, context)

# Общая функция для показа прогресса
async def show_progress_common(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Получен user_id: {user_id}")

    # Инициализация данных пользователя, если их нет
    if user_id not in user_progress:
        user_progress[user_id] = {"cases_solved": 0, "last_case": None}
        logger.info(f"Инициализированы данные для пользователя {user_id}")

    progress = user_progress.get(user_id, {"cases_solved": 0})
    logger.info(f"Отправка прогресса для пользователя {user_id}: {progress['cases_solved']} кейсов")
    await update.message.reply_text(
        f"Вы решили {progress['cases_solved']} кейсов.",
        reply_markup=get_reply_keyboard()
    )

# Команда /progress
async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_progress_common(update, context)

# Обработка кнопки "Показать прогресс"
async def handle_progress_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Кнопка 'Показать прогресс' нажата")
    await show_progress_common(update, context)

# Функция для отправки счета через Telegram Payments API
async def send_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Параметры счета
    title = "Подписка Simple"
    description = "Оплата подписки на месяц (300 кейсов)"
    payload = "payment_payload_simple"  # Уникальный идентификатор платежа
    provider_token = "424924419:LIVE:4"  # Токен провайдера платежей (ЮKassa)
    currency = "RUB"  # Валюта
    price = 85000  # Цена в копейках (850 рублей)

    try:
        # Отправляем счет
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=[LabeledPrice("К оплате", price)],
            need_name=True,  # Запрашивать имя пользователя
            need_phone_number=True,  # Запрашивать номер телефона
            need_email=True,  # Запрашивать email
        )
        logger.info(f"Счет отправлен пользователю {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке счета: {e}")
        await update.message.reply_text("Произошла ошибка при отправке счета.")

# Обработчик предварительного запроса на оплату
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    try:
        # Подтверждаем предварительный запрос
        await query.answer(ok=True)
        logger.info(f"Предварительный запрос на оплату подтвержден для пользователя {query.from_user.id}")
    except Exception as e:
        # Если произошла ошибка, отправляем отказ
        await query.answer(ok=False, error_message=str(e))
        logger.error(f"Ошибка при обработке предварительного запроса: {e}")

# Обработчик успешной оплаты
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment_info = update.message.successful_payment
    user_id = update.effective_user.id

    # Логируем успешную оплату
    logger.info(f"Пользователь {user_id} успешно оплатил: {payment_info.total_amount} {payment_info.currency}")

    # Сохраняем номер транзакции из ЮKassa
    provider_payment_charge_id = payment_info.provider_payment_charge_id
    logger.info(f"Номер транзакции в ЮKassa: {provider_payment_charge_id}")

    # Здесь можно добавить логику для активации услуги или предоставления контента
    await update.message.reply_text(
        "Спасибо за оплату! Теперь у вас есть доступ к расширенным возможностям."
    )

# Команда /pay
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_invoice(update, context)

# Обработка кнопки "Оплатить доступ"
async def handle_pay_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_invoice(update, context)


# Основная функция
def main():
    logger.info("Запуск бота")
    TELEGRAM_TOKEN = '7521673360:AAFAjbx3fHud3M85BBrksZFsJ2E9gwi-zeo'
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("case", get_case))
    application.add_handler(CommandHandler("progress", show_progress))
    application.add_handler(CommandHandler("pay", send_payment_invoice))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.Regex("^Показать прогресс$"), handle_progress_button))
    application.add_handler(MessageHandler(filters.Regex("^Оплатить доступ$"), handle_pay_button))
    application.add_handler(MessageHandler(filters.Regex("^Тарифы$"), handle_tariffs_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_solution))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))


    application.run_polling()

if __name__ == '__main__':
    main()