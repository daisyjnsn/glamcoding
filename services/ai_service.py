import re
import openai
from openai import AsyncOpenAI
from utils.logger import logger
import time
import random
from dotenv import load_dotenv
import os

load_dotenv()
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

openai.api_key = DEEPSEEK_API_KEY
llmDS = AsyncOpenAI(
    base_url="https://api.deepseek.com",
    api_key='sk-d1672acd035f46dc808392e1efda3fe9',
)


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


parameters = {
    'difficulty': 'сложный',
    'level': 'новичок'
}


async def generateCase():
    unique_param = f"cache_buster={time.time()}_{random.randint(1000, 9999)}"
    try:
        response = await llmDS.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": taskPrompt},
                {"role": "user", "content": 
                             f"Сложность кейса: {parameters['difficulty']}"
                             f"Уровень пользователя: {parameters['level']}"
                            #  f"Сгенерируй кейс для КПТ-психотерапевта"
                             f"{unique_param}"
                 }
            ],
            temperature=1.5,
            top_p=0.9,
            stream=False
        )
    
    except Exception as e:
        ...