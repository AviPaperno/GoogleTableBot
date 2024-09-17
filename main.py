import asyncio

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN
from questionExtractor import Quizzer

router = Router()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
quizzer = Quizzer()


class CurrentQuiz(StatesGroup):
    start = State()
    choosing_test = State()
    question = State()


def create_keyboard(options):
    """Функция для создания клавиатуры из списка возможных вариантов"""
    return types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text=f"{elem}")] for elem in options])


async def ask_question(message: types.Message, state: FSMContext):
    """Функция для отправки вопроса с формированием клавиатуры ответов"""
    data = await state.get_data()
    question = data["current_question"]
    keyboard = create_keyboard(question["answers"])
    await message.answer(question["question"], reply_markup=keyboard)
    await state.update_data(current_question=question)
    await state.update_data(choosing_test=data["choosing_test"][1:])


# Обработчик на команду старт. Стейт CurrentQuiz.start
@router.message(CurrentQuiz.start)
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    keyboard = create_keyboard(quizzer.get_topics().keys())
    await message.answer("Привет, я бот Quizzer. Вот доступные темы для тестов. Выбери любую", reply_markup=keyboard)
    await state.set_state(CurrentQuiz.choosing_test)


# Обработчик стейта выбора теста
@router.message(CurrentQuiz.choosing_test, F.text.in_(quizzer.get_topics().keys()))
async def start_quizz(message: types.Message, state: FSMContext):
    chosen_test_title = message.text
    choosing_test = quizzer.questions_and_answers(message.text)

    await state.update_data(
        choosing_test=choosing_test,
        current_question=choosing_test[0]
    )

    await message.answer(f"Выбрана тема: {chosen_test_title}")
    await state.set_state(CurrentQuiz.question)
    await ask_question(message, state)


@router.message(CurrentQuiz.question)
async def getting_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    quizzer.write_answer_to_result_cell(
        message.from_user.username,
        data["current_question"]["question"],
        message.text,
        f'{data["current_question"]["correct_answer"]}'
    )

    remaining_questions = data["choosing_test"]

    if remaining_questions:
        await state.update_data(choosing_test=remaining_questions, current_question=remaining_questions[0])
        await ask_question(message, state)
    else:
        await state.clear()
        await message.answer("Все вопросы закончились", reply_markup=create_keyboard(["Выбрать новый квиз"]))
        await state.set_state(CurrentQuiz.start)


# Запуск процесса поллинга новых апдейтов
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
