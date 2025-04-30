from aiogram import types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
# from services.db_service import initialize_user_progress


def getReplyKeyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text='Показать прогресс'),
        KeyboardButton(text='Оплатить доступ'),
        KeyboardButton(text='Тарифы'),
        KeyboardButton(text='Получить/отправить кейс'),
    )
    keyboard.adjust(2)
    
    return keyboard.as_markup(resize_keyboard=True, one_time_keyboard=False)


async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    welcomeMessage = (
        "Привет, я <b>BTrainer</b>. Я помогаю КПТ-психотерапевтам улучшать свои профессиональные навыки с помощью практики на сгенерированных кейсах.\n\n"
        "Для получения кейса:\n"
        "- Нажми на кнопку <b>Получить кейс</b> или отправь команду <b>/case</b>.\n\n"
        "Чтобы узнать стоимость подписки:\n"
        "- Нажми на кнопку <b>Тарифы</b> или отправь команду <b>/tariffs</b>.\n\n"
        "Также ты можешь наблюдать за своим прогрессом в решении кейсов:\n"
        "- Нажми на кнопку <b>Показать прогресс</b> или отправь команду <b>/progress</b>."
    )
    await message.answer(welcomeMessage, reply_markup=getReplyKeyboard(), parse_mode='HTML')


def regStartHandlers(dp):
    dp.message.register(start, Command('start'))
