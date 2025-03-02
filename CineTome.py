import time
import telebot
from telebot import types
from collections import Counter

API_TOKEN = '8074690974:AAEydE9h-g7CLOB2udL02i0v4YDf43gCc2A'
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
        "Add Movie", "Add Book", "List Movies", "List Books",
        "Recommend", "Stats", "Change Status"
    ]
    markup.add(*[types.KeyboardButton(btn) for btn in buttons])
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user_state.pop(chat_id, None)
    bot.reply_to(message, "Давай начнем, выбери из меню и поехали", reply_markup=create_main_menu())

@bot.message_handler(commands=['list_movies'])
def list_movies(message):
    if not data["movies"]:
        bot.send_message(message.chat.id, "Ваш список фильмов пуст.")
        return
    response = "Ваш список фильмов:\n" + "\n".join(
        f"{idx+1}. {m['title']} – {m['status']} (Жанр: {m['genre']})"
        for idx, m in enumerate(data["movies"])
    )
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['list_books'])
def list_books(message):
    if not data["books"]:
        bot.send_message(message.chat.id, "Ваш список книг пуст.")
        return
    response = "Ваш список книг:\n" + "\n".join(
        f"{idx+1}. {b['title']} – {b['status']} (Жанр: {b['genre']})"
        for idx, b in enumerate(data["books"])
    )
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['change_status'])
def change_status(message):
    chat_id = message.chat.id
    all_items = data["movies"] + data["books"]
    if not all_items:
        bot.send_message(chat_id, "Ваш список пуст.")
        return
    markup = types.InlineKeyboardMarkup()
    for item in all_items:
        markup.add(types.InlineKeyboardButton(item["title"], callback_data=f"change_{item['title']}"))
    bot.send_message(chat_id, "Выберите элемент для изменения статуса:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_"))
def callback_change_status(call):
    chat_id = call.message.chat.id
    item_name = call.data[len("change_"):].strip()
    item = next((i for i in data["movies"] + data["books"] if i["title"] == item_name), None)
    if not item:
        bot.answer_callback_query(call.id, "Ошибка: элемент не найден.")
        return
    markup = types.InlineKeyboardMarkup()
    statuses = ["хочу посмотреть/прочитать", "в процессе", "уже посмотрел/прочитал"]
    for status in statuses:
        if status != item["status"]:
            markup.add(types.InlineKeyboardButton(status, callback_data=f"update_{item_name}_{status}"))
    bot.send_message(chat_id, f"Выберите новый статус для '{item_name}':", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("update_"))
def callback_update_status(call):
    chat_id = call.message.chat.id
    _, item_name, new_status = call.data.split("_", 2)
    item = next((i for i in data["movies"] + data["books"] if i["title"] == item_name), None)
    if item:
        item["status"] = new_status
        bot.send_message(chat_id, f"Статус '{item_name}' обновлен: {new_status}")
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, "Ошибка: элемент не найден.")

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)
