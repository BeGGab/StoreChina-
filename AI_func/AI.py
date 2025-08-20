import telebot
from telebot import types
import json
import requests
import random
from datetime import datetime
import time

bot = telebot.TeleBot('8127036562:AAHDyx_ygbhVOTXrQcAqRlifYStmb1vDLMA')

# Mock данные для демонстрации
MOCK_PRODUCTS = [
    {
        'id': 1,
        'name': 'Умные часы SmartWatch Pro',
        'price': 1250,
        'image': 'https://via.placeholder.com/300x300/4A90E2/white?text=SmartWatch',
        'rating': 4.8,
        'sales': 12500,
        'store': 'Official Store'
    },
    {
        'id': 2,
        'name': 'Беспроводные наушники',
        'price': 890,
        'image': 'https://via.placeholder.com/300x300/50C878/white?text=Headphones',
        'rating': 4.6,
        'sales': 8900,
        'store': 'TechGadgets'
    },
    {
        'id': 3,
        'name': 'Портативная колонка',
        'price': 670,
        'image': 'https://via.placeholder.com/300x300/FF6B6B/white?text=Speaker',
        'rating': 4.5,
        'sales': 5600,
        'store': 'AudioPro'
    },
    {
        'id': 4,
        'name': 'Смартфон Xiaomi',
        'price': 15400,
        'image': 'https://via.placeholder.com/300x300/FFA500/white?text=Xiaomi',
        'rating': 4.7,
        'sales': 23400,
        'store': 'Xiaomi Official'
    },
    {
        'id': 5,
        'name': 'Ноутбук игровой',
        'price': 45600,
        'image': 'https://via.placeholder.com/300x300/9370DB/white?text=Laptop',
        'rating': 4.9,
        'sales': 1200,
        'store': 'GamingTech'
    },
    {
        'id': 6,
        'name': 'Фитнес-браслет',
        'price': 560,
        'image': 'https://via.placeholder.com/300x300/20B2AA/white?text=Fitness',
        'rating': 4.4,
        'sales': 8900,
        'store': 'HealthCare'
    }
]

user_carts = {}


class AIProductSearch:
    @staticmethod
    def search_products(query):
        """Имитация AI поиска товаров"""
        query = query.lower()
        filtered_products = [
            p for p in MOCK_PRODUCTS
            if query in p['name'].lower() or query in p['store'].lower()
        ]

        if not filtered_products:
            filtered_products = random.sample(MOCK_PRODUCTS, min(4, len(MOCK_PRODUCTS)))

        return filtered_products


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🛍️ Открыть маркетплейс'))
    markup.add(types.KeyboardButton('🔍 Поиск товаров'))
    markup.add(types.KeyboardButton('🛒 Корзина'))

    bot.send_message(
        message.chat.id,
        "🎉 Добро пожаловать в AI Taobao Assistant!\n\n"
        "Я помогу вам найти лучшие товары на Taobao с помощью искусственного интеллекта!",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == '🛍️ Открыть маркетплейс')
def open_marketplace(message):
    markup = types.InlineKeyboardMarkup()
    web_app_btn = types.InlineKeyboardButton(
        text='🚀 Открыть мини-приложение',
        web_app=types.WebAppInfo(url='https://beggab.github.io/StoreChina-/')
    )
    markup.add(web_app_btn)

    bot.send_message(
        message.chat.id,
        "Нажмите кнопку ниже, чтобы открыть AI маркетплейс:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == '🔍 Поиск товаров')
def search_products(message):
    msg = bot.send_message(message.chat.id, "🔍 Что вы ищете на Taobao?")
    bot.register_next_step_handler(msg, process_search_query)


def process_search_query(message):
    query = message.text.strip()
    if not query:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите поисковый запрос")
        return

    bot.send_chat_action(message.chat.id, 'typing')

    # Имитация AI поиска
    products = AIProductSearch.search_products(query)

    if not products:
        bot.send_message(message.chat.id, "😔 Ничего не найдено. Попробуйте другой запрос")
        return

    # Отправляем товары по одному с задержкой
    for i, product in enumerate(products):
        if i % 2 == 0 and i + 1 < len(products):
            # Отправляем пару товаров в одном сообщении
            send_product_pair_safe(message.chat.id, products[i], products[i + 1])
        elif i % 2 == 0:
            # Отправляем одиночный товар
            send_single_product(message.chat.id, products[i])

        # Небольшая задержка между сообщениями
        time.sleep(0.5)


def send_product_pair_safe(chat_id, product1, product2):
    """Безопасная отправка пары товаров без media_group"""
    try:
        # Сначала отправляем первое фото
        photo_msg1 = bot.send_photo(chat_id, product1['image'])

        # Затем второе фото
        photo_msg2 = bot.send_photo(chat_id, product2['image'])

        # Отправляем описание для обоих товаров
        caption = (
            f"🛍️ **{product1['name']}**\n"
            f"💰 {product1['price']}₽ • ⭐ {product1['rating']}\n"
            f"🏪 {product1['store']}\n\n"
            f"🛍️ **{product2['name']}**\n"
            f"💰 {product2['price']}₽ • ⭐ {product2['rating']}\n"
            f"🏪 {product2['store']}"
        )

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(
            f"🛒 {product1['price']}₽",
            callback_data=f"add_{product1['id']}"
        )
        btn2 = types.InlineKeyboardButton(
            f"🛒 {product2['price']}₽",
            callback_data=f"add_{product2['id']}"
        )
        markup.row(btn1, btn2)

        bot.send_message(chat_id, caption, parse_mode='Markdown', reply_markup=markup)

    except Exception as e:
        print(f"Ошибка при отправке пары товаров: {e}")
        # Fallback: отправляем товары по отдельности
        send_single_product(chat_id, product1)
        send_single_product(chat_id, product2)


def send_single_product(chat_id, product):
    """Отправка одиночного товара"""
    try:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(
            f"🛒 Добавить в корзину - {product['price']}₽",
            callback_data=f"add_{product['id']}"
        )
        markup.add(btn)

        caption = (
            f"🛍️ **{product['name']}**\n\n"
            f"💰 Цена: {product['price']}₽\n"
            f"⭐ Рейтинг: {product['rating']}\n"
            f"📦 Продано: {product['sales']} шт.\n"
            f"🏪 Магазин: {product['store']}"
        )

        bot.send_photo(chat_id, product['image'], caption=caption,
                       parse_mode='Markdown', reply_markup=markup)

    except Exception as e:
        print(f"Ошибка при отправке товара: {e}")
        # Отправляем только текст, если фото не загружается
        caption = (
            f"🛍️ **{product['name']}**\n\n"
            f"💰 Цена: {product['price']}₽\n"
            f"⭐ Рейтинг: {product['rating']}\n"
            f"📦 Продано: {product['sales']} шт.\n"
            f"🏪 Магазин: {product['store']}\n"
            f"📸 Фото временно недоступно"
        )

        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(
            f"🛒 Добавить в корзину - {product['price']}₽",
            callback_data=f"add_{product['id']}"
        )
        markup.add(btn)

        bot.send_message(chat_id, caption, parse_mode='Markdown', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def add_to_cart(call):
    try:
        product_id = int(call.data.split('_')[1])
        user_id = call.from_user.id

        product = next((p for p in MOCK_PRODUCTS if p['id'] == product_id), None)

        if not product:
            bot.answer_callback_query(call.id, "❌ Товар не найден")
            return

        if user_id not in user_carts:
            user_carts[user_id] = []

        user_carts[user_id].append(product)

        bot.answer_callback_query(call.id, f"✅ {product['name']} добавлен в корзину!")

    except Exception as e:
        print(f"Ошибка при добавлении в корзину: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при добавлении в корзину")


@bot.message_handler(func=lambda message: message.text == '🛒 Корзина')
def show_cart(message):
    try:
        user_id = message.from_user.id

        if user_id not in user_carts or not user_carts[user_id]:
            bot.send_message(message.chat.id, "🛒 Ваша корзина пуста")
            return

        cart = user_carts[user_id]
        total = sum(item['price'] for item in cart)

        cart_text = "🛒 **Ваша корзина:**\n\n"
        for i, item in enumerate(cart, 1):
            cart_text += f"{i}. {item['name']} - {item['price']}₽\n"

        cart_text += f"\n💵 **Итого: {total}₽**"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"))
        markup.add(types.InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart"))

        bot.send_message(message.chat.id, cart_text, parse_mode='Markdown', reply_markup=markup)

    except Exception as e:
        print(f"Ошибка при показе корзины: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при загрузке корзины")


@bot.callback_query_handler(func=lambda call: call.data == 'checkout')
def checkout(call):
    try:
        user_id = call.from_user.id

        if user_id not in user_carts or not user_carts[user_id]:
            bot.answer_callback_query(call.id, "❌ Корзина пуста")
            return

        total = sum(item['price'] for item in user_carts[user_id])

        bot.send_message(
            call.message.chat.id,
            f"🎉 Заказ оформлен!\n\n"
            f"💵 Сумма: {total}₽\n"
            f"📦 Товаров: {len(user_carts[user_id])}\n"
            f"🕐 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Спасибо за покупку! 🛍️"
        )

        # Очищаем корзину
        user_carts[user_id] = []

    except Exception as e:
        print(f"Ошибка при оформлении заказа: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при оформлении заказа")


@bot.callback_query_handler(func=lambda call: call.data == 'clear_cart')
def clear_cart(call):
    try:
        user_id = call.from_user.id

        if user_id in user_carts:
            user_carts[user_id] = []

        bot.answer_callback_query(call.id, "🗑️ Корзина очищена")
        bot.edit_message_text("🛒 Корзина очищена", call.message.chat.id, call.message.message_id)

    except Exception as e:
        print(f"Ошибка при очистке корзины: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при очистке корзины")


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🤖 **AI Taobao Assistant - Помощь**

🛍️ **Возможности:**
- AI поиск товаров на Taobao
- Умные рекомендации
- Корзина покупок
- Быстрое оформление заказов

📋 **Команды:**
/start - Запустить бота
/help - Помощь

🎯 **Как использовать:**
1. Нажмите "🔍 Поиск товаров"
2. Введите что ищете
3. Выбирайте товары из результатов
4. Добавляйте в корзину
5. Оформляйте заказ!
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')


# Обработчик ошибок
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ Неизвестная команда. Используйте /help")


if __name__ == '__main__':
    print("🤖 AI Taobao Bot запущен...")
    try:
        bot.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
