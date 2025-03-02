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

    markup.add(btn_add_movie, btn_add_book)
    markup.add(btn_list_movies, btn_list_books)
    markup.add(btn_recommend, btn_stats)
    markup.add(btn_change_status)
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    if chat_id in user_state:
        user_state.pop(chat_id)

    text = (
        "Давай начнем, выбери из меню и поехали"
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
    user_state[chat_id] = {
        "action": "movie",
        "step": "awaiting_title"
    }
    bot.send_message(chat_id, "Введите название фильма:")

@bot.message_handler(commands=['add_book'])
def handle_add_book(message):
    chat_id = message.chat.id
    user_state[chat_id] = {
        "action": "book",
        "step": "awaiting_title"
    }
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
        data["movies"].append({
            "title": item_name,
            "genre": item_genre,
            "status": item_status
        })
        bot.send_message(chat_id, f"Фильм '{item_name}' добавлен.\nЖанр: {item_genre}, Статус: {item_status}")
    else:
        data["books"].append({
            "title": item_name,
            "genre": item_genre,
            "status": item_status
        })
        bot.send_message(chat_id, f"Книга '{item_name}' добавлена.\nЖанр: {item_genre}, Статус: {item_status}")

    user_state.pop(chat_id, None)
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['list_movies'])
def list_movies(message):
    if not data["movies"]:
        bot.send_message(message.chat.id, "Ваш список фильмов пуст.")
        return
    response = "Ваш список фильмов:\n"
    for idx, movie in enumerate(data["movies"], start=1):
        response += f"{idx}. {movie['title']} – {movie['status']} (Жанр: {movie['genre']})\n"
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['list_books'])
def list_books(message):
    if not data["books"]:
        bot.send_message(message.chat.id, "Ваш список книг пуст.")
        return
    response = "Ваш список книг:\n"
    for idx, book in enumerate(data["books"], start=1):
        response += f"{idx}. {book['title']} – {book['status']} (Жанр: {book['genre']})\n"
    bot.send_message(message.chat.id, response)

def get_most_popular_genre():
    """
    Определяем самый популярный жанр у пользователя.
    Если списки пусты, возвращаем None.
    """
    all_genres = []
    for movie in data["movies"]:
        all_genres.append(movie["genre"])
    for book in data["books"]:
        all_genres.append(book["genre"])

    if not all_genres:
        return None

    counter = Counter(all_genres)
    most_common = counter.most_common(1)[0][0]
    return most_common

def user_has_item(title):
    """
    Проверяем, есть ли у пользователя элемент с таким названием.
    """
    for movie in data["movies"]:
        if movie["title"].lower() == title.lower():
            return True
    for book in data["books"]:
        if book["title"].lower() == title.lower():
            return True
    return False

@bot.message_handler(commands=['recommend'])
def recommend(message):
    """
    Расширенная логика рекомендаций:
    1) Определяем самый популярный жанр у пользователя.
    2) Берём из recommendation_db[жанр] элемент, которого нет у пользователя.
    3) Если ничего не найдено, пробуем другой жанр или выводим, что рекомендаций нет.
    """
    popular_genre = get_most_popular_genre()

    if not popular_genre:
        bot.send_message(message.chat.id, "У вас пока нет фильмов или книг. Добавьте что-нибудь для рекомендаций.")
        return

    possible_recs = recommendation_db.get(popular_genre, [])

    filtered_recs = [item for item in possible_recs if not user_has_item(item["title"])]

    if filtered_recs:

        rec = filtered_recs[0]
        if rec["type"] == "movie":
            bot.send_message(message.chat.id, f"Рекомендуем фильм в жанре '{popular_genre}': {rec['title']}")
        else:
            bot.send_message(message.chat.id, f"Рекомендуем книгу в жанре '{popular_genre}': {rec['title']}")
    else:
        fallback_recs = recommendation_db.get("не указано", [])

        if fallback_recs:
            alt = fallback_recs[0]
            bot.send_message(message.chat.id,
                             f"У вас уже есть все рекомендации по жанру '{popular_genre}'.\n"
                             f"Попробуйте это: {alt['title']}")
        else:
            bot.send_message(message.chat.id, "У нас нет дополнительных рекомендаций по вашим жанрам.")

@bot.message_handler(commands=['stats'])
def stats(message):
    num_movies = len(data["movies"])
    num_books = len(data["books"])
    response = (
        f"Статистика:\n"
        f"Фильмов: {num_movies}\n"
        f"Книг: {num_books}\n"
    )
    bot.send_message(message.chat.id, response)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_"))
def callback_change_status(call):
    chat_id = call.message.chat.id
    item_name = call.data[len("change_"):].strip()

    # Найдем элемент в списке
    item = None
    for i in data["movies"] + data["books"]:
        if i["title"].strip().lower() == item_name.lower():
            item = i
            break

    if not item:
        bot.answer_callback_query(call.id, "Ошибка: элемент не найден.")
        return

    current_status = item["status"]

    # Определяем, какие кнопки показывать в зависимости от текущего статуса
    markup = types.InlineKeyboardMarkup()
    
    if current_status == "в процессе":
        markup.add(types.InlineKeyboardButton("Хочу посмотреть", callback_data=f"update_{item_name}_want"))
        markup.add(types.InlineKeyboardButton("Уже посмотрел/прочитал", callback_data=f"update_{item_name}_done"))
    elif current_status == "хочу посмотреть/прочитать":
        markup.add(types.InlineKeyboardButton("В процессе", callback_data=f"update_{item_name}_in_progress"))
        markup.add(types.InlineKeyboardButton("Уже посмотрел/прочитал", callback_data=f"update_{item_name}_done"))
    elif current_status == "уже посмотрел/прочитал":
        markup.add(types.InlineKeyboardButton("В процессе", callback_data=f"update_{item_name}_in_progress"))
        markup.add(types.InlineKeyboardButton("Хочу посмотреть", callback_data=f"update_{item_name}_want"))

    bot.send_message(chat_id, f"Выберите новый статус для '{item_name}':", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("update_"))
def callback_update_status(call):
    chat_id = call.message.chat.id

    # Найдем последний "_" для отделения названия от статуса
    last_underscore = call.data.rfind("_")
    if last_underscore == -1:
        bot.answer_callback_query(call.id, "Ошибка обновления статуса.")
        return

    # Разбираем название и новый статус
    item_name = call.data[7:last_underscore].strip()  # Берем название (7 - длина "update_")
    new_status = call.data[last_underscore + 1:].strip()  # Берем статус

    status_map = {
        "want": "хочу посмотреть/прочитать",
        "in_progress": "в процессе",
        "done": "уже посмотрел/прочитал"
    }

    # Проверяем, является ли новый статус допустимым
    if new_status not in status_map:
        bot.answer_callback_query(call.id, "Ошибка: некорректный статус.")
        return

    updated_status = status_map[new_status]

    # Логируем данные для отладки
    print(f"Полученное название: {item_name}, новый статус: {updated_status}")
    print("Доступные элементы:")
    for item in data["movies"] + data["books"]:
        print(f"- {item['title']} (статус: {item['status']})")

    # Ищем элемент в списке
    for item in data["movies"] + data["books"]:
        if item["title"].strip().lower() == item_name.lower():
            item["status"] = updated_status
            bot.send_message(chat_id, f"Статус '{item_name}' обновлен: {updated_status}")
            bot.answer_callback_query(call.id)
            return

    bot.answer_callback_query(call.id, "Ошибка: элемент не найден.")

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)