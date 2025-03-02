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
    btn_add_movie = types.KeyboardButton("Add Movie")
    btn_add_book = types.KeyboardButton("Add Book")
    btn_list_movies = types.KeyboardButton("List Movies")
    btn_list_books = types.KeyboardButton("List Books")
    btn_recommend = types.KeyboardButton("Recommend")
    btn_stats = types.KeyboardButton("Stats")
    btn_change_status = types.KeyboardButton("Change Status")
    markup.add(btn_add_movie, btn_add_book, btn_list_movies, btn_list_books, btn_recommend, btn_stats, btn_change_status)
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user_state.pop(chat_id, None)
    bot.reply_to(message, "Давай начнем, выбери из меню и поехали", reply_markup=create_main_menu())

def get_list(data_type):
    if not data[data_type]:
        return "Список пуст."
    response = "Ваш список {}:\n".format("фильмов" if data_type == "movies" else "книг")
    for idx, item in enumerate(data[data_type], start=1):
        response += f"{idx}. {item['title']} – {item['status']} (Жанр: {item['genre']})\n"
    return response

@bot.message_handler(func=lambda msg: msg.text in ["List Movies", "List Books"])
def list_items(message):
    data_type = "movies" if message.text == "List Movies" else "books"
    bot.send_message(message.chat.id, get_list(data_type))

def find_item(title):
    for category in ["movies", "books"]:
        for item in data[category]:
            if item["title"].lower() == title.lower():
                return item
    return None

@bot.message_handler(func=lambda msg: msg.text == "Change Status")
def change_status(message):
    items = data["movies"] + data["books"]
    if not items:
        bot.send_message(message.chat.id, "У вас пока нет фильмов или книг в списке.")
        return
    markup = types.InlineKeyboardMarkup()
    for item in items:
        markup.add(types.InlineKeyboardButton(item["title"], callback_data=f"change_{item['title']}"))
    bot.send_message(message.chat.id, "Выберите элемент для изменения статуса:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_"))
def callback_change_status(call):
    chat_id = call.message.chat.id
    item_name = call.data[len("change_") :].strip()
    item = find_item(item_name)
    if not item:
        bot.answer_callback_query(call.id, "Ошибка: элемент не найден.")
        return
    markup = types.InlineKeyboardMarkup()
    status_options = [
        ("Хочу посмотреть/прочитать", "want"),
        ("В процессе", "in_progress"),
        ("Уже посмотрел/прочитал", "done")
    ]
    for text, status in status_options:
        markup.add(types.InlineKeyboardButton(text, callback_data=f"update_{item_name}_{status}"))
    bot.send_message(chat_id, f"Выберите новый статус для '{item_name}':", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("update_"))
def callback_update_status(call):
    chat_id = call.message.chat.id
    _, item_name, new_status = call.data.split("_", 2)
    item = find_item(item_name)
    if not item:
        bot.answer_callback_query(call.id, "Ошибка: элемент не найден.")
        return
    status_map = {
        "want": "хочу посмотреть/прочитать",
        "in_progress": "в процессе",
        "done": "уже посмотрел/прочитал"
    }
    item["status"] = status_map[new_status]
    bot.send_message(chat_id, f"Статус '{item_name}' обновлен: {status_map[new_status]}")
    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)