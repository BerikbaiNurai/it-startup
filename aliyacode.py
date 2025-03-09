import time
import telebot
from telebot import types
from collections import Counter

API_TOKEN = '8046948508:AAECKT-b6OHkjp-zQzKytySknoOzBdZWTSc'
bot = telebot.TeleBot(API_TOKEN)

recommendation_db = {
    "фентези": [
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

    markup.add(btn_add_movie, btn_add_book)
    markup.add(btn_list_movies, btn_list_books)
    markup.add(btn_recommend, btn_stats)
    markup.add(btn_change_status)
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    if chat_id not in user_state:
        user_state[chat_id] = {"movies": [], "books": []}

    text = (
        "Скоро в Telegram: ваш личный помощник для управления фильмами и книгами!\n\n"
        "Используйте команды или кнопки меню:\n"
        "/add_movie, /add_book, /list_movies, /list_books, /recommend, /stats, /change_status\n\n"
        "Или нажмите на нужную кнопку ниже:"
    )
    menu = create_main_menu()
    bot.reply_to(message, text, reply_markup=menu)

@bot.message_handler(func=lambda msg: msg.text in [
    "Add Movie", "Add Book", "List Movies", "List Books",
    "Recommend", "Stats", "Change Status"
])
def handle_menu_buttons(message):
    if message.text == "Add Movie":
        handle_add_movie(message)
    elif message.text == "Add Book":
        handle_add_book(message)
    elif message.text == "List Movies":
        list_movies(message)
    elif message.text == "List Books":
        list_books(message)
    elif message.text == "Recommend":
        recommend(message)
    elif message.text == "Stats":
        stats(message)
    elif message.text == "Change Status":
        change_status(message)

@bot.message_handler(commands=['add_movie'])
def handle_add_movie(message):
    chat_id = message.chat.id
    user_state[chat_id]["action"] = "movie"
    user_state[chat_id]["step"] = "awaiting_title"
    bot.send_message(chat_id, "Введите название фильма:")

@bot.message_handler(commands=['add_book'])
def handle_add_book(message):
    chat_id = message.chat.id
    user_state[chat_id]["action"] = "book"
    user_state[chat_id]["step"] = "awaiting_title"
    bot.send_message(chat_id, "Введите название книги:")

@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith('/'), content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id)

    if not state:
        bot.send_message(chat_id, "Используйте /add_movie или /add_book (или меню) чтобы добавить элемент.")
        return

    action = state["action"]
    step = state["step"]

    if step == "awaiting_title":
        user_state[chat_id]["item_name"] = message.text.strip()
        user_state[chat_id]["step"] = "awaiting_genre"
        bot.send_message(chat_id, "Введите жанр:")

    elif step == "awaiting_genre":
        user_state[chat_id]["genre"] = message.text.strip().lower()
        user_state[chat_id]["step"] = "awaiting_status"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Хочу посмотреть/прочитать", callback_data="status_want"))
        markup.add(types.InlineKeyboardButton("В процессе", callback_data="status_in_progress"))
        markup.add(types.InlineKeyboardButton("Уже посмотрел/прочитал", callback_data="status_done"))

        bot.send_message(chat_id, "Выберите статус:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("status_"))
def callback_status(call):
    chat_id = call.message.chat.id
    state = user_state.get(chat_id)

    if not state:
        bot.answer_callback_query(call.id, "Ошибка. Попробуйте снова.")
        return

    status_map = {
        "status_want": "хочу посмотреть/прочитать",
        "status_in_progress": "в процессе",
        "status_done": "уже посмотрел/прочитал"
    }
    item_status = status_map[call.data]

    action = state["action"]
    item_name = state["item_name"]
    item_genre = state["genre"]

    if action == "movie":
        user_state[chat_id]["movies"].append({
            "title": item_name,
            "genre": item_genre,
            "status": item_status
        })
        bot.send_message(chat_id, f"Фильм '{item_name}' добавлен.\nЖанр: {item_genre}, Статус: {item_status}")
    else:
        user_state[chat_id]["books"].append({
            "title": item_name,
            "genre": item_genre,
            "status": item_status
        })
        bot.send_message(chat_id, f"Книга '{item_name}' добавлена.\nЖанр: {item_genre}, Статус: {item_status}")

    user_state[chat_id]["step"] = None
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['list_movies'])
def list_movies(message):
    chat_id = message.chat.id
    if chat_id not in user_state or not user_state[chat_id]["movies"]:
        bot.send_message(chat_id, "Ваш список фильмов пуст.")
        return
    response = "Ваш список фильмов:\n"
    for idx, movie in enumerate(user_state[chat_id]["movies"], start=1):
        response += f"{idx}. {movie['title']} – {movie['status']} (Жанр: {movie['genre']})\n"
    bot.send_message(chat_id, response)

@bot.message_handler(commands=['list_books'])
def list_books(message):
    chat_id = message.chat.id
    if chat_id not in user_state or not user_state[chat_id]["books"]:
        bot.send_message(chat_id, "Ваш список книг пуст.")
        return
    response = "Ваш список книг:\n"
    for idx, book in enumerate(user_state[chat_id]["books"], start=1):
        response += f"{idx}. {book['title']} – {book['status']} (Жанр: {book['genre']})\n"
    bot.send_message(chat_id, response)

@bot.message_handler(commands=['recommend'])
def recommend(message):
    chat_id = message.chat.id
    if chat_id not in user_state or (not user_state[chat_id]["movies"] and not user_state[chat_id]["books"]):
        bot.send_message(chat_id, "Добавьте хотя бы один фильм или книгу для рекомендаций.")
        return

    all_genres = []
    for movie in user_state[chat_id]["movies"]:
        all_genres.append(movie["genre"])
    for book in user_state[chat_id]["books"]:
        all_genres.append(book["genre"])

    if not all_genres:
        bot.send_message(chat_id, "Похоже, у вас нет жанров для рекомендаций.")
        return

    most_common_genre = Counter(all_genres).most_common(1)[0][0]
    recommendations = recommendation_db.get(most_common_genre, [])

    if recommendations:
        rec = recommendations[0]
        if rec["type"] == "movie":
            bot.send_message(chat_id, f"Рекомендуем фильм в жанре {most_common_genre}: {rec['title']}")
        else:
            bot.send_message(chat_id, f"Рекомендуем книгу в жанре {most_common_genre}: {rec['title']}")
    else:
        bot.send_message(chat_id, "К сожалению, у нас нет рекомендаций для этого жанра.")

@bot.message_handler(commands=['stats'])
def stats(message):
    chat_id = message.chat.id
    if chat_id not in user_state:
        bot.send_message(chat_id, "У вас нет данных.")
        return
    num_movies = len(user_state[chat_id]["movies"])
    num_books = len(user_state[chat_id]["books"])
    response = (
        f"Статистика:\n"
        f"Фильмов: {num_movies}\n"
        f"Книг: {num_books}\n"
    )
    bot.send_message(chat_id, response)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)
