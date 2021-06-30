import sqlite3
import time
import telebot
from telebot import types

from config import initialize

bot = initialize()


def init():
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	cursor.execute("""CREATE TABLE if not exists shop
                      (name text, image_link text, description text,
                       price number)
                   """)

	cursor.execute("""CREATE TABLE if not exists wallet
                        (telegram_id number, username text, balance number default 0)
                    """)
	cursor.execute("""CREATE TABLE if not exists steps
	                        (telegram_id number, username text, step text default 'new', status text default 'wait')
	                    """)
	conn.close()

def bd_change(query):
	try:
		conn = sqlite3.connect("mydatabase.db")
		cursor = conn.cursor()
		cursor.execute(query)
		conn.commit()
		conn.close()
		return 0
	except:
		conn.close()
	return 1

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
	print(call)
	if call.data == f'catalog{call.data[-1:]}':
		bot.edit_message_reply_markup(chat_id=call.message.chat.id,
									  message_id=call.message.message_id,
									  reply_markup=catalog_keyboard(int(call.data[-1:])))
	elif call.data[:3] == 'buy':
		buy_product(call)
	elif call.data == 'back':
		bot.delete_message(call.message.chat.id, call.message.message_id)
	elif call.data == 'null':
		pass
	else:
		send_product(call.data[:-1], call.message.chat)


@bot.message_handler(commands=['start'])
def send_welcome(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	if not cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = {message.from_user.id}""").fetchall():
		cursor.execute(f"""INSERT INTO wallet ('telegram_id', 'username') VALUES ('{message.from_user.id}', 'anonymus')""")
		cursor.execute(f"""INSERT INTO steps ('telegram_id', 'username') VALUES ('{message.from_user.id}', 'anonymus')""")
		conn.commit()
	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton(text="Каталог", callback_data='catalog0'))
	bot.send_photo(message.from_user.id, open('img/blackmarket.png', 'rb'), reply_markup=keyboard)
	conn.close()

def catalog_keyboard(page):
	keyboard = types.InlineKeyboardMarkup()
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	products = cursor.execute("""SELECT * FROM shop""").fetchall()
	conn.close()
	products_count = len(products)
	i = 0 + 10 * page
	while i <= (page + 1) * 10:
		if i >= products_count:
			break
		keyboard.add(types.InlineKeyboardButton(text=f"{products[i][0]} {products[i][3]}$",
												callback_data=f'{products[i][0] + str(page)}'))
		i += 1
	return add_catalog_footer(keyboard, page)


def add_catalog_footer(keyboard, page):
	if page == 0:
		keyboard.row(types.InlineKeyboardButton(text=f"{page + 1}/4", callback_data='null'),
					 types.InlineKeyboardButton(text=">", callback_data=f'catalog{page + 1}'))
	elif page == 3:
		keyboard.row(types.InlineKeyboardButton(text="<", callback_data=f'catalog{page - 1}'),
					 types.InlineKeyboardButton(text=f"{page + 1}/4", callback_data='null'))
	else:
		keyboard.row(types.InlineKeyboardButton(text="<", callback_data=f'catalog{page - 1}'),
					 types.InlineKeyboardButton(text=f"{page + 1}/4", callback_data='null'),
					 types.InlineKeyboardButton(text=">", callback_data=f'catalog{page + 1}'))
	return keyboard


def send_product(product, chat):
	keyboard = types.InlineKeyboardMarkup()
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	entity = cursor.execute(f"""SELECT * FROM shop WHERE name = '{product}'""").fetchall()[0]
	conn.close()
	keyboard.add(types.InlineKeyboardButton(text=f"Купить {entity[3]}", callback_data=f'buy{product}'))
	keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data='back'))
	bot.send_photo(chat_id=chat.id, photo=open(entity[1], 'rb'), caption=entity[2], reply_markup=keyboard)


def buy_product(call):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	balance = cursor.execute(f"SELECT * FROM wallet WHERE telegram_id = '{call.from_user.id}'").fetchall()[0][2]
	price = cursor.execute(f"SELECT * FROM shop WHERE name = '{call.data[3:]}'").fetchall()[0][3]
	if balance >= price:
		cursor.execute(f"""UPDATE wallet SET balance = {balance - price} WHERE telegram_id = {call.from_user.id}""")
		conn.commit()
		conn.close()
		bot.send_message(call.message.chat.id, f"Поздравляю. Вы купили {call.data[3:]}!\nНомер вашего заказа:\n3cb50a7b990798c0559b9032b5f8586f7de223217528591d6f3dce959180038b")
	else:
		conn.close()
		bot.send_message(call.message.chat.id, "Прошу прощения, но у вас недостаточно денег.")
		time.sleep(2)
		bot.send_message(call.message.chat.id, "Если вам нужны деньги, то у меня для вас предложение. Пришлите мне /job и я расскажу более детально.")

@bot.message_handler(commands=['job'])
def job(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	task = {
		1: {
			'text': "Это ваше первое задание:\nhttps://www.ditsib-puzzle-challenge.com/path3/0eb49da3-3d6d-49be-8f45-104c1c2c69ed\nКроме продажи необычных вещей, я еще выполняю разные заказы.\nОдин из моих клиентов попросил меня расшифровать это.\nПришлите мне ответ, когда закончите.",
			'answer': "bankingsystem"},
		2: {
			'text': "Это ваше второе задание:\nhttps://www.ditsib-puzzle-challenge.com/path3/c499cce0-79e6-446b-9a3a-b90421ab7828\nДругой мой клиент зашифровал ключ от своего цифрового кошелька, но забыл как расшифровывать его.\nОн готов заплатить большие деньги за расшифровку. Я буду ждать от вас ключ от кошелька.",
			'answer': "1c62590c99871030411c60c4780da31ec05c4db349e2f02d79c01228fccd9380"},
		3: {
			'text': "Это ваше третье задание:\n((BV80605001911AP)- (sqrt(-1)))^2\nЕсли честно, мне стыдно просить вас об этом, но не могли бы вы помочь с домашним заданием моей дочери?\nЯ где-то видел эту задачу, но не могу вспомнить ее решение.\nЯ буду ждать число.",
			'answer': "-16"}}
	if not cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = {message.from_user.id}""").fetchall():
		cursor.execute(f"""INSERT INTO wallet ('telegram_id', 'username') VALUES ('{message.from_user.id}', 'anonymus')""")
		cursor.execute(f"""INSERT INTO steps ('telegram_id', 'username') VALUES ('{message.from_user.id}', 'anonymus')""")
		conn.commit()
		conn.close()
		return send_welcome(message)
	step = cursor.execute(f"""SELECT step FROM steps WHERE telegram_id = '{message.from_user.id}'""").fetchone()[0]
	if step == 'new':
		bd_change(f"""UPDATE steps SET step = 'first' WHERE telegram_id = {message.from_user.id}""")
	if step == 'first':
		bot.send_message(message.chat.id, task[1]['text'])
		bd_change(f"""UPDATE steps SET status = 'work' WHERE telegram_id = {message.from_user.id}""")
	elif step == 'second':
		bot.send_message(message.chat.id, task[2]['text'])
		bd_change(f"""UPDATE steps SET status = 'work' WHERE telegram_id = {message.from_user.id}""")
	elif step == 'third':
		bot.send_message(message.chat.id, task[3]['text'])
		bd_change(f"""UPDATE steps SET status = 'work' WHERE telegram_id = {message.from_user.id}""")
	elif step == 'passed':
		bot.send_message(message.chat.id, 'Вы уже выполнили все мои задания! Теперь вы можете купить то, что вам нужно.')
	conn.close()


@bot.message_handler(func=lambda message: True, content_types=['text'])
def quest(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	task = {
		1: {
			'text': "Это ваше первое задание:\nhttps://www.ditsib-puzzle-challenge.com/path3/0eb49da3-3d6d-49be-8f45-104c1c2c69ed\nКроме продажи необычных вещей, я еще выполняю разные заказы.\nОдин из моих клиентов попросил меня расшифровать это.\nПришлите мне ответ, когда закончите.",
			'answer': "bankingsystem"},
		2: {
			'text': "Это ваше второе задание:\nhttps://www.ditsib-puzzle-challenge.com/path3/c499cce0-79e6-446b-9a3a-b90421ab7828\nДругой мой клиент зашифровал ключ от своего цифрового кошелька, но забыл как расшифровывать его.\nОн готов заплатить большие деньги за расшифровку. Я буду ждать от вас ключ от кошелька.",
			'answer': "1c62590c99871030411c60c4780da31ec05c4db349e2f02d79c01228fccd9380"},
		3: {
			'text': "Это ваше третье задание:\n((BV80605001911AP)- (sqrt(-1)))^2\nЕсли честно, мне стыдно просить вас об этом, но не могли бы вы помочь с домашним заданием моей дочери?\nЯ где-то видел эту задачу, но не могу вспомнить ее решение.\nЯ буду ждать число.",
			'answer': "-16"}}
	if not cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = {message.from_user.id}""").fetchall():
		cursor.execute(f"""INSERT INTO wallet ('telegram_id', 'username') VALUES ('{message.from_user.id}', 'anonymus')""")
		cursor.execute(f"""INSERT INTO steps ('telegram_id', 'username') VALUES ('{message.from_user.id}', 'anonymus')""")
		conn.commit()
		conn.close()
		return send_welcome(message)
	step = cursor.execute(f"""SELECT step FROM steps WHERE telegram_id = '{message.from_user.id}'""").fetchone()[0]
	status = cursor.execute(f"""SELECT status FROM steps WHERE telegram_id = '{message.from_user.id}'""").fetchone()[0]
	if step == 'new':
		return
	if status == 'wait':
		return
	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{message.from_user.id}'""").fetchall()[0][1]
	chat_id = message.chat.id
	if step == 'first':
		if message.text == task[1]['answer']:
			bd_change(f"""UPDATE steps SET step = 'second' WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE steps SET status = 'wait' WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE wallet SET balance = 3000 WHERE telegram_id = {message.from_user.id}""")
			bot.send_message(message.chat.id, 'Хорошая работа! Вы заработали 3000$. Пришлите мне /job , чтобы получить следующее задание.')
		else:
			bot.send_message(message.chat.id, 'Неправильный ответ! Попробуйте еще раз.')
	elif step == 'second':
		if message.text == task[2]['answer']:
			bd_change(f"""UPDATE steps SET step = 'third' WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE steps SET status = 'wait' WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE wallet SET balance = 6000 WHERE telegram_id = {message.from_user.id}""")
			bot.send_message(message.chat.id, 'Хорошая работа! Вы заработали 3000$. Пришлите мне /job , чтобы получить следующее задание.')
		else:
			bot.send_message(message.chat.id, 'Неправильный ответ! Попробуйте еще раз.')
	elif step == 'third':
		if message.text == task[3]['answer']:
			bd_change(f"""UPDATE steps SET step = 'passed' WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE wallet SET balance = 9000 WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE steps SET status = 'wait' WHERE telegram_id = {message.from_user.id}""")
			bot.send_message(message.chat.id, 'Хорошая работа! Вы заработали 3000$. Вы выполнили все мои задачи. Можете приступить к покупкам.')
			send_welcome(message)
		else:
			bot.send_message(message.chat.id, 'Неправильный ответ! Попробуйте еще раз.')
	else:
		pass
	conn.commit()
	conn.close()

init()
bot.polling()
