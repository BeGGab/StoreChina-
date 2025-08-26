# bot.py
import telebot
from telebot import types
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Токен (тестовый)
TOKEN = '8127036562:AAHDyx_ygbhVOTXrQcAqRlifYStmb1vDLMA'
ADMIN_ID = 1707332723

bot = telebot.TeleBot(TOKEN)

# Подключаем функции из database.py
import database

# Инициализация БД при старте
if __name__ == '__main__':
    database.init_db()


# =============================================
# ФУНКЦИИ
# =============================================

def send_admin_notification(user_info, order_data, order_id):
    """Уведомление админа"""
    try:
        name = user_info.get('name') or user_info.get('first_name') or 'Клиент'
        message = f"🔔 НОВЫЙ ЗАКАЗ! #{order_id}\n\n"
        message += f"👤 {name}\n"
        if user_info.get('phone'):
            message += f"📞 {user_info['phone']}\n"
        if user_info.get('address'):
            message += f"🏠 {user_info['address']}\n"
        message += f"🆔 {user_info['id']}\n"
        if user_info.get('username'):
            message += f"• @{user_info['username']}\n"

        message += f"\n📦 Сумма: {order_data['total']}₽ ({len(order_data['items'])} шт)\n"
        message += "📋 Состав:\n"
        for i, item in enumerate(order_data['items'], 1):
            qty = item.get('quantity', 1)
            message += f"{i}. {item['name']} - {item['price']}₽ x{qty}\n"

        bot.send_message(ADMIN_ID, message)
        logger.info("Уведомление админу отправлено")
    except Exception as e:
        logger.error("Ошибка отправки уведомления: %s", e)


# =============================================
# ОБРАБОТЧИКИ
# =============================================

@bot.message_handler(commands=['start'])
def start(message):
    logger.info("/start от %s", message.from_user.id)

    # Регистрируем пользователя (без контактов — только Telegram-данные)
    database.register_or_update_customer(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        username=message.from_user.username
    )

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Открыть маркетплейс'))

    bot.send_message(
        message.chat.id,
        "Добро пожаловать в AI Taobao Assistant!\n\n"
        "Нажмите кнопку ниже чтобы открыть мини-приложение с маркетплейсом:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == 'Открыть маркетплейс')
def open_marketplace(message):
    logger.info("Открытие маркетплейса %s", message.from_user.id)

    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url='https://beggab.github.io/StoreChina-/')
    button = types.InlineKeyboardButton(text='Открыть магазин', web_app=web_app)
    markup.add(button)

    bot.send_message(
        message.chat.id,
        "🛒 Нажмите кнопку ниже чтобы открыть магазин:",
        reply_markup=markup
    )


@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        logger.info("WEB_APP_DATA от %s", message.from_user.id)
        logger.info("Raw data: %s", message.web_app_data.data)

        # Валидация
        try:
            data = json.loads(message.web_app_data.data)
        except json.JSONDecodeError:
            bot.send_message(message.chat.id, "❌ Ошибка: неверные данные")
            return

        if not isinstance(data, dict) or data.get('action') != 'checkout':
            bot.send_message(message.chat.id, "❌ Неверный тип данных")
            return

        user_data = data.get('user', {})
        try:
            total = float(data.get('total', 0))
        except (TypeError, ValueError):
            total = 0.0
        items = data.get('items', [])
        if not items:
            bot.send_message(message.chat.id, "❌ Корзина пуста")
            return

        # Информация из Telegram
        telegram_user_info = {
            'id': message.from_user.id,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'username': message.from_user.username
        }
        full_user_info = {**telegram_user_info, **user_data}

        # Гарантируем имя
        if not full_user_info.get('name'):
            full_user_info['name'] = full_user_info.get('first_name') or 'Клиент'

        order_data = {
            'items': items,
            'total': round(total, 2),
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        }

        # Сохраняем заказ (автоматически обновит профиль)
        order_id = database.save_order(full_user_info, order_data)
        if not order_id:
            bot.send_message(message.chat.id, "❌ Ошибка сохранения заказа")
            return

        # Уведомление админу
        send_admin_notification(full_user_info, order_data, order_id)

        # Подтверждение клиенту
        bot.send_message(
            message.chat.id,
            f"✅ Заказ №{order_id} оформлен!\n\n"
            f"💵 Сумма: {total}₽\n"
            f"📦 Товаров: {len(items)}\n\n"
            f"Администратор свяжется с вами для подтверждения."
        )

    except Exception as e:
        logger.error("Ошибка обработки WebApp: %s", e)
        bot.send_message(message.chat.id, "❌ Ошибка обработки заказа")


@bot.message_handler(commands=['orders'])
def show_orders(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Только для администратора")
        return

    orders = database.get_recent_orders(10)
    if not orders:
        bot.send_message(message.chat.id, "📭 Нет заказов")
        return

    text = "📦 Последние заказы:\n\n"
    for o in orders:
        addr = (o.get('delivery_address') or 'Не указан')[:30]
        text += (
            f"#{o['id_order']} | {o['total_amount_rub']}₽ | {o['order_date']}\n"
            f"👤 {o['full_name']} | 📞 {o.get('phone', 'нет')}\n"
            f"📍 {addr}...\n"
            f"📊 {o['status']}\n"
            "➖➖➖\n"
        )
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['status'])
def status(message):
    stats = database.get_stats()
    info = (
        f"🤖 Статус бота\n"
        f"👥 Пользователей: {stats['users']}\n"
        f"📦 Заказов: {stats['orders']}\n"
        f"🕒 {datetime.now().strftime('%H:%M:%S')}"
    )
    bot.send_message(message.chat.id, info)


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🤖 AI Taobao Assistant - Помощь

/start - Запустить
/help - Помощь
/status - Статус
/orders - Заказы (админ)
    """
    bot.send_message(message.chat.id, help_text)


# =============================================
# ЗАПУСК
# =============================================

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Бот запущен")
    logger.info("Админ ID: %s", ADMIN_ID)
    logger.info("=" * 50)

    try:
        bot.polling(none_stop=True, interval=1, timeout=30)
    except Exception as e:
        logger.error("Ошибка бота: %s", e)
