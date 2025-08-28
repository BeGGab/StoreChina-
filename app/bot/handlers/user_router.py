from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.api.dao import UserDAO
import app.bot.keyboards.kbs as kb
from app.bot.utils import greet_user

user_router = Router()


class Registration(StatesGroup):
    """Состояния для процесса регистрации."""
    waiting_for_phone = State()


@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Обрабатывает команду /start.
    """
    user = await UserDAO.find_one_or_none(telegram_id=message.from_user.id)

    if not user:
        await message.answer(
            f'Привет Дорогой Покупатель! 👋\n'
            f'Я твой телеграмм AI-помошник для TaoBao 😊\n'
        )
        # Предварительная регистрация пользователя без номера телефона
        await UserDAO.register_or_update(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username
        )
        await message.answer(
            '☎️ Для продолжения, пожалуйста, поделитесь вашим номером телефона.',
            # Предполагается, что kb.clients_phone() создает клавиатуру с кнопкой request_contact
            reply_markup=await kb.clients_phone()
        )
        await state.set_state(Registration.waiting_for_phone)
    else:
        # Если пользователь уже есть, просто приветствуем
        await greet_user(message, is_new_user=False)


@user_router.message(Registration.waiting_for_phone, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """
    Обрабатывает получение номера телефона и завершает регистрацию.
    """
    # Убедимся, что пользователь отправил свой собственный контакт
    if message.contact.user_id != message.from_user.id:
        await message.answer("Пожалуйста, отправьте свой контакт, а не чужой.")
        return

    # Обновляем данные пользователя с номером телефона
    await UserDAO.register_or_update(
        telegram_id=message.from_user.id,
        phone=message.contact.phone_number
    )
    await state.clear()
    await message.answer("Спасибо! Ваш номер телефона сохранен.")
    # Теперь, когда регистрация завершена, приветствуем пользователя
    await greet_user(message, is_new_user=True)


@user_router.message(Registration.waiting_for_phone)
async def process_contact_invalid(message: Message):
    """
    Обрабатывает неверный ввод, когда бот ожидает номер телефона.
    """
    await message.answer("Пожалуйста, используйте кнопку ниже, чтобы поделиться вашим номером телефона.")


@user_router.message(F.text == '🔙 Назад')
async def cmd_back_home(message: Message) -> None:
    """
    Обрабатывает нажатие кнопки "Назад".
    """
    await greet_user(message, is_new_user=False)

'''@user_router.message(F.text == "ℹ️ О нас")
async def about_us(message: Message):
    kb = kb.app_keyboard(user_id=message.from_user.id, first_name=message.from_user.first_name)
    await message.answer(get_about_us_text(), reply_markup=kb)'''