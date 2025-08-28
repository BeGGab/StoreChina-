from aiogram.types import ReplyKeyboardMarkup, WebAppInfo, InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from app.config import settings



def main_keyboard(user_id: int, first_name: str) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    url_applications = f"{settings.BASE_SITE}/applications?user_id={user_id}"
    url_add_application = f'{settings.BASE_SITE}/form?user_id={user_id}&first_name={first_name}'
    kb.button(text="🛍 Мои покупки", web_app=WebAppInfo(url=url_applications))
    kb.button(text="🔍 Поиск товара", web_app=WebAppInfo(url=url_add_application))
    kb.button(text="ℹ️ О нас")
    if user_id == settings.ADMIN_ID:
        kb.button(text="🔑 Админ панель")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

 
def back_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔙 Назад")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def admin_keyboard(user_id: int) -> InlineKeyboardMarkup:
    url_applications = f"{settings.BASE_SITE}/admin?admin_id={user_id}"
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 На главную", callback_data="back_home")
    kb.button(text="📝 Смотреть заявки", web_app=WebAppInfo(url=url_applications))
    kb.adjust(1)
    return kb.as_markup()


def app_keyboard(user_id: int, first_name: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    url_add_application = f'{settings.BASE_SITE}/form?user_id={user_id}&first_name={first_name}'
    kb.button(text="🔍 Поиск товара", web_app=WebAppInfo(url=url_add_application))
    kb.adjust(1)
    return kb.as_markup()

async def clients_name(name):
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=name)]],
                               resize_keyboard=True,
                               input_field_placeholder='Введите имя или оставьте такое же ⬇️')


async def clients_phone():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='☎️ Поделиться контактом', request_contact=True)]],
                               resize_keyboard=True,
                               input_field_placeholder='Введите номер или поделитесь контактом ⬇️')


async def clients_location():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📍 Отправить геолокацию',
                                                         request_location=True)]],
                               resize_keyboard=True,
                               input_field_placeholder='Введите адрес или отправьте геолокацию ⬇️')