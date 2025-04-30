from aiogram import types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.ai_service import generateCase#, analyzeSolution
# from services.db_service import get_user_progress, update_user_progress


class BotStates(StatesGroup):
    waitingForSolution = State()


def getInlineKeyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Получить новый кейс', callback_data='getCase'))

    return keyboard.as_markup()


async def getCase(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    case = generateCase()
    # get_user_progress(user_id)['lastCase'] = case

    await message.answer(
        f'Ваш новый терапевтический кейс:\n{case}\nВведите ваше решение.',
        reply_markup=getInlineKeyboard()
    )
    await state.set_state(BotStates.waitingForSolution)


# async def handleSolution(message: types.Message, state: FSMContext):
#     user_id = message.from_user.id
#     user_solution = message.text
#     # last_case = get_user_progress(user_id).get("last_case")
    
#     if not last_case:
#         await message.answer(
#             "Сначала получите кейс с помощью команды /case.",
#             reply_markup=get_reply_keyboard()
#         )
#         await state.clear()
#         return
    
#     analysis = analyze_solution(last_case, user_solution)
#     # update_user_progress(user_id, cases_solved=1)
#     await message.answer(
#         f"Анализ вашего решения:\n{analysis}",
#         reply_markup=get_inline_keyboard()
#     )
#     await state.clear()


def regChatHandlers(dp):
    dp.message.register(getCase, Command('case'))
    # dp.message.register(handleSolution, BotStates.waitingForSolution)
