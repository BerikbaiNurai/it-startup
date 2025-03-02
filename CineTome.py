import time
import json
import telebot
from telebot import types
from collections import Counter

API_TOKEN = 'YOUR_BOT_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

recommendation_db = {
    "фэнтези": [
        {"title": "Гарри Поттер и Тайная комната", "type": "movie"},
        {"title": "Властелин колец: Братство кольца", "type": "movie"},
        {"title": "Хроники Нарнии", "type": "book"},
    ],
    "фантастика": [
        {"title": "Интерстеллар", "type": "movie"},
        {"title": "Дюна", "type": "book"},
        {"title": "Звёздные войны: Новая надежда", "type": "movie"},
    ],
    "романтика": [
        {"title": "Тетрадь", "type": "movie"},
        {"title": "Гордость и предубеждение", "type": "book"}
    ],
    "не указано": [
        {"title": "Универсальная рекомендация", "type": "movie"}
    ]
}

data = {
    "movies": [],
    "books": []
}

user_state = {}

def create_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        "Add Movie", "Add Book", "List Movies", "List Books", "Recommend", "Stats", "Change Status"
    ]
    markup.add(*(types.KeyboardButton(text) for text in buttons))
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user_state.pop(chat_id, None)
    text = "Ваш личный помощник для управления фильмами и книгами!"
    bot.send_message(chat_id, text, reply_markup=create_main_menu())

@bot.message_handler(commands=['change_status'])
def change_status(message):
    chat_id = message.chat.id
    items = data["movies"] + data["books"]
    if not items:
        bot.send_message(chat_id, "Ваш список пуст.")
        return
    
    markup = types.InlineKeyboardMarkup()
    for item in items:
        callback_data = json.dumps({"action": "change", "title": item["title"]})
        markup.add(types.InlineKeyboardButton(f"{item['title']} ({item['status']})", callback_data=callback_data))
    bot.send_message(chat_id, "Выберите фильм или книгу для изменения статуса:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_change_status(call):
    try:
        data_callback = json.loads(call.data)
        if data_callback.get("action") == "change":
            item_name = data_callback["title"]
            markup = types.InlineKeyboardMarkup()
            for status_key, status_text in {"in_progress": "В процессе", "done": "Уже посмотрел/прочитал"}.items():
                markup.add(types.InlineKeyboardButton(status_text, callback_data=json.dumps({"action": "update", "title": item_name, "status": status_key})))
            bot.send_message(call.message.chat.id, f"Выберите новый статус для '{item_name}':", reply_markup=markup)
        elif data_callback.get("action") == "update":
            item_name = data_callback["title"]
            new_status = {"in_progress": "в процессе", "done": "уже посмотрел/прочитал"}[data_callback["status"]]
            for item in data["movies"] + data["books"]:
                if item["title"] == item_name:
                    item["status"] = new_status
                    bot.send_message(call.message.chat.id, f"Статус '{item_name}' обновлен: {new_status}")
                    break
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ошибка: {e}")

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)