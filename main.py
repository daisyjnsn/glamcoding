from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import BotCommand
import asyncio
from dotenv import load_dotenv
import os
from utils.logger import setupLogger
from handlers.chat_handler import regChatHandlers
from handlers.start_handler import regStartHandlers


load_dotenv()

BOT_API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


bot = Bot(BOT_API_TOKEN)
dp = Dispatcher()

setupLogger()

regStartHandlers(dp)
regChatHandlers(dp)


async def setBotCommnds():
    commands = [
        BotCommand(command='start', description='Начать работу'),
        BotCommand(command='case', description='Получить новый кйес'),
        BotCommand(command='progress', description='Показать прогресс'),
        BotCommand(command='tariffs', description='Тарифы'),
        BotCommand(command='pay', description='Оплатить доступ')
    ]

    await bot.set_my_commands(commands)


# @dp.message(F.text)
# async def generate_streamed_response(message: types.Message):
#     sent_message = await message.answer("Генерирую ответ...")
#     full_response = ""
#     buffer = ""
#     last_update_time = asyncio.get_event_loop().time()

#     try:
#         stream = await llmDS.chat.completions.create(
#             model="deepseek-chat",
#             messages=[{"role": "user", "content": message.text}],
#             stream=True
#         )

#         async for chunk in stream:
#             if chunk.choices and chunk.choices[0].delta.content:
#                 content = chunk.choices[0].delta.content
#                 full_response += content
#                 buffer += content

#                 # Обновляем сообщение, если буфер достиг 100 символов или прошло 1 секунда
#                 current_time = asyncio.get_event_loop().time()
#                 if len(buffer) >= 100 or (current_time - last_update_time) >= 1:
#                     await bot.edit_message_text(
#                         chat_id=sent_message.chat.id,
#                         message_id=sent_message.message_id,
#                         text=full_response + "..."
#                     )
#                     buffer = ""  # Очищаем буфер
#                     last_update_time = current_time  # Обновляем время последнего обновления

#                 await asyncio.sleep(1)

#         # Убираем многоточие после завершения генерации
#         await bot.edit_message_text(
#             chat_id=sent_message.chat.id,
#             message_id=sent_message.message_id,
#             text=full_response
#         )

#     except Exception as e:
#         await bot.edit_message_text(
#             chat_id=sent_message.chat.id,
#             message_id=sent_message.message_id,
#             text=f"Произошла ошибка: {str(e)}"
#         )


# @dp.message(F.text)
# async def generateCase(message: types.Message):
#     sentMessage = await message.answer('Генерирую ответ...')

    
#         # print(response)

#         await bot.edit_message_text(
#             chat_id=sentMessage.chat.id,
#             message_id=sentMessage.message_id,
#             text=response.choices[0].message.content
#             )
    
#     except Exception as e:
#         await bot.edit_message_text(
#             chat_id=sentMessage.chat.id,
#             message_id=sentMessage.message_id,
#             text=f"Произошла ошибка: {str(e)}"
#         )


async def main():
    await setBotCommnds()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
