from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.logger import logger
import logging
import re
import asyncio
import os
from openai import AsyncOpenAI, api_key
from dotenv import load_dotenv
import time
import random


load_dotenv()

# Initialize bot and dispatcher
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
PAYMENT_URL = os.getenv('PAYMENT_URL')

api_key = DEEPSEEK_API_KEY
llmDS = AsyncOpenAI(
    base_url="https://api.deepseek.com",
    api_key='sk-d1672acd035f46dc808392e1efda3fe9',
)


bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Logging configuration

# User progress storage (in-memory, replace with a database in production)
user_progress = {}


taskPrompt = (
            "Ты — помощник для студентов-психологов, обучающихся когнитивно-поведенческой терапии. "
            "Ты отлично владеешь знаниями об общей психологии, этическими принципами психолога, теоретическими и практическими знаниями о когнитивно-поведенческой терапии. "
            "Отвечай только на вопросы, связанные с психологией. Если вопрос не относится к теме психологии, вежливо укажи пользователю, что он может задавать вопросы только на эту тему. "
            "Сгенерируй короткий терапевтический кейс для практики и ожидай решения пользователя. "
            "Кейс должен включать только название и описание кейса без целей терапии и других подробностей. "
            "Кейс должен быть основан на принципах КПТ и учитывать типичные проблемы, встречающиеся на практике психолога. "
            # "Пример содержания для вдохновения: " + book_content + " "
            "ВАЖНО: Текст должен быть максимально простым и читаемым. "
            "НЕ используй никакие стили форматирования текста, такие как **жирный шрифт**, *курсив*, HTML-теги или скобки (**, [], и т.д.). "
            "Пример правильного формата: "
            '"Название кейса: Страх публичных выступлений у студента. '
            'Описание: Клиент — студент 3 курса, 21 год. Обратился с жалобой на сильный страх перед публичными выступлениями..."'
        )


analyzePrompt = (
    """
    Ты — эксперт по КПТ. Твоя задача — анализировать решения студентов, которые работают с клиническими кейсами.
    Оценивай их ответы на предмет соответствия принципам КПТ, корректности использования техник и терминологии.
    Давай конструктивную обратную связь: указывай сильные стороны и предлагай улучшения.'
    НЕ используй никакие стили форматирования текста, такие как **жирный шрифт**, *курсив*, HTML-теги или скобки (**, [], и т.д.). 
    """
)


parameters = {
    'difficulty': 'сложный',
    'level': 'новичок'
}


# Define states for FSM (Finite State Machine)
class BotStates(StatesGroup):
    waiting_for_solution = State()

# Helper functions for keyboards
def get_inline_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Получить новый кейс", callback_data="get_case"))
    return keyboard.as_markup()

def get_reply_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text="Показать прогресс"),
        KeyboardButton(text="Оплатить доступ"),
        KeyboardButton(text="Тарифы"),
        KeyboardButton(text="Получить кейс")
    )
    keyboard.adjust(2)  # Arrange buttons in 2 columns
    return keyboard.as_markup(resize_keyboard=True, one_time_keyboard=False)

# Start command handler
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user_progress[user_id] = {"cases_solved": 0, "last_case": None}
    logger.info("Отправка приветственного сообщения с выпадающим меню.")
    welcome_message = (
        "Привет, я <b>BTrainer</b>. Я помогаю КПТ-психотерапевтам улучшать свои профессиональные навыки с помощью практики на сгенерированных кейсах.\n\n"
        "Для получения кейса:\n"
        "- Нажми на кнопку <b>Получить кейс</b> или отправь команду <b>/case</b>.\n\n"
        "Чтобы узнать стоимость подписки:\n"
        "- Нажми на кнопку <b>Тарифы</b> или отправь команду <b>/tariffs</b>.\n\n"
        "Также ты можешь наблюдать за своим прогрессом в решении кейсов:\n"
        "- Нажми на кнопку <b>Показать прогресс</b> или отправь команду <b>/progress</b>."
    )
    await message.answer(welcome_message, reply_markup=get_reply_keyboard(), parse_mode="HTML")

# Callback query handler
@dp.callback_query(F.data == "get_case")
async def button_handler(query: types.CallbackQuery, state: FSMContext):
    logger.info(f"Нажата кнопка: {query.data}")
    await query.answer()
    await send_case_common(query.message, state)



# Function to generate a therapeutic case
async def generateCase(message: types.Message):
    full_response = "Ваш новый терапевтический кейс:\n"
    buffer = ""
    last_update_time = asyncio.get_event_loop().time()
    unique_param = f"cache_buster={time.time()}_{random.randint(1000, 9999)}"

    while True:
        try:
            stream = await llmDS.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": taskPrompt},
                    {"role": "user", "content": 
                                f"Сложность кейса: {parameters['difficulty']}"
                                f"Уровень пользователя: {parameters['level']}"
                                f"{unique_param}"
                    }
                ],
                temperature=1.5,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    buffer += content

                    current_time = asyncio.get_event_loop().time()
                    if len(buffer) >= 100 or (current_time - last_update_time) >= 1:
                        await bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            text=full_response + "..."
                        )
                        buffer = ""
                        last_update_time = current_time

                    await asyncio.sleep(0.2)

            full_response += '\nВведите ваше решение'
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=full_response,
            )
            return full_response

        except Exception as e:
            if "Too Many Requests" in str(e) or "429" in str(e):
                retry_after = 60
                try:
                    retry_after = int(str(e).split("Retry-After: ")[1].split()[0])
                except:
                    pass

                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=f"Превышен лимит запросов. Пожалуйста, подождите {retry_after} секунд..."
                )

                await asyncio.sleep(retry_after)

                continue

            else:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=f"Произошла ошибка: {str(e)}"
                )

                return full_response



# Common function to send a case
async def send_case_common(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    logger.info(f"Получен user_id: {user_id}")
    if user_id not in user_progress:
        user_progress[user_id] = {"cases_solved": 0, "last_case": None}
        logger.info(f"Инициализированы данные для пользователя {user_id}")

    
    baseMessage = await message.answer('Генерирую ответ...')
    case = await generateCase(baseMessage)
    user_progress[user_id]["last_case"] = case
    await state.set_state(BotStates.waiting_for_solution)


# Handler for user solutions
@dp.message(BotStates.waiting_for_solution)
async def handle_solution(message: types.Message, state: FSMContext):
    if len(message.text.split()) < 10:
        await message.answer('Ваше решение слишком короткое')
        return
    
    user_id = message.chat.id
    last_case = user_progress.get(user_id, {}).get("last_case")
    
    if not last_case:
        logger.warning(f"Пользователь {user_id} попытался отправить решение без активного кейса")
        await message.answer(
            "Сначала получите кейс с помощью команды /case.",
            reply_markup=get_reply_keyboard()
        )
        await state.clear()
        return
    
    sysMessage = await message.answer('Анализ вашего решения:\n')

    await analyze_solution(message, sysMessage)
    user_progress[user_id]["cases_solved"] += 1
    await state.clear()
    logger.info(f"Анализ решения успешно выполнен!")

# Function to analyze solution (simulated)
async def analyze_solution(userMessage: types.Message, sysMessage: types.Message):
    full_response = sysMessage.text + '\n'
    buffer = ""
    last_update_time = asyncio.get_event_loop().time()
    unique_param = f"cache_buster={time.time()}_{random.randint(1000, 9999)}"
    user_id = userMessage.from_user.id
    logger.info(userMessage.text)

    while True:
        try:
            # Создаем потоковый запрос к модели
            stream = await llmDS.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": analyzePrompt},
                        {"role": "user", "content":
                                            f'Кейс: {user_progress[user_id]['last_case']}'
                                            f'Решение: {userMessage.text}'
                                            f'{unique_param}'   
                        }
                    ],
                    temperature=1,
                    stream=True
                )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    buffer += content

                    current_time = asyncio.get_event_loop().time()
                    if len(buffer) >= 100 or (current_time - last_update_time) >= 1.5:
                        await bot.edit_message_text(
                            chat_id=sysMessage.chat.id,
                            message_id=sysMessage.message_id,
                            text=full_response + "..."
                        )
                        buffer = ""
                        last_update_time = current_time

                    await asyncio.sleep(0.3)

            # full_response += '\nВведите ваше решение'
            await bot.edit_message_text(
                chat_id=sysMessage.chat.id,
                message_id=sysMessage.message_id,
                text=full_response,
                reply_markup=get_inline_keyboard()
            )
            return full_response

        except Exception as e:
            if "Too Many Requests" in str(e) or "429" in str(e):
                retry_after = 60
                try:
                    retry_after = int(str(e).split("Retry-After: ")[1].split()[0])
                except:
                    pass

                await bot.edit_message_text(
                    chat_id=sysMessage.chat.id,
                    message_id=sysMessage.message_id,
                    text=f"Превышен лимит запросов. Пожалуйста, подождите {retry_after} секунд..."
                )

                await asyncio.sleep(retry_after)

                continue

            else:
                await bot.edit_message_text(
                    chat_id=sysMessage.chat.id,
                    message_id=sysMessage.message_id,
                    text=f"Произошла ошибка: {str(e)}"
                )
                return full_response

# Tariffs command handler
@dp.message(Command("tariffs"))
async def tariffs(message: types.Message):
    tariffs_info = (
        "Наши тарифы:\n"
        "1. Simple — 850 руб/мес\n"
        "   - около 300 кейсов в месяц\n"
        "2. Profi — скоро появится\n"
        "Для оплаты нажми на кнопку Оплатить доступ или отправь команду /pay"
    )
    await message.answer(tariffs_info, reply_markup=get_reply_keyboard())

# Progress command handler
@dp.message(Command("progress"))
async def show_progress(message: types.Message):
    user_id = message.chat.id
    progress = user_progress.get(user_id, {"cases_solved": 0})
    await message.answer(
        f"Вы решили {progress['cases_solved']} кейсов.",
        reply_markup=get_reply_keyboard()
    )

# Pay command handler
@dp.message(Command("pay"))
async def pay(message: types.Message):
    payment_url = PAYMENT_URL  # Replace with real payment link
    await message.answer(
        f"Для получения расширенного доступа перейдите по ссылке: {payment_url}",
        reply_markup=get_reply_keyboard()
    )


@dp.message(lambda message: message.text == 'Показать прогресс')
async def showProgress(message: types.Message, state: FSMContext):
    await show_progress(message)


@dp.message(lambda message: message.text == 'Тарифы')
async def showTariffs(message: types.Message, state: FSMContext):
    await tariffs(message)


@dp.message(lambda message: message.text == 'Оплатить доступ')
async def payFor(message: types.Message, state: FSMContext):
    await pay(message)


@dp.message(lambda message: message.text == 'Получить кейс')
async def getCase(message: types.Message, state: FSMContext):
    await send_case_common(message, state)


@dp.message(lambda message: message.text == 'Получить новый кейс')
async def getNewCase(message: types.Message, state: FSMContext):
    await send_case_common(message, state)


@dp.callback_query(F.data == 'Получить новый кейс')
async def showProgress(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await show_progress(query.message)


@dp.message(Command('case'))
async def case(message: types.Message, state: FSMContext):
    await send_case_common(message, state)


# Main entry point
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
