import sqlite3
import telebot
import time
from telebot import types

bot = telebot.TeleBot("1312594008:AAEcU-eiJJ_r1d57mA4Wnha3Kv14qf3cVsk")


def init():
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	cursor.execute("""CREATE TABLE if not exists shop
                      (name text, image_link text, description text,
                       price number)
                   """)

	cursor.execute("""CREATE TABLE if not exists wallet
                        (telegram_id number, balance number)
                    """)
	conn.close()


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{call.from_user.id}'""").fetchall()[0][1]
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
	elif call.data == 'Yes':
			job(call)
	elif call.data == 'No':
		pass
	else:
		send_product(call.data[:-1], call.message.chat)


@bot.message_handler(commands=['start'])
def send_welcome(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	if not cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = {message.from_user.id}""").fetchall():
		cursor.execute(f"""INSERT INTO wallet VALUES ({message.from_user.id}, 0)""")
		conn.commit()
	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton(text="Catalog", callback_data='catalog0'))
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
	keyboard.add(types.InlineKeyboardButton(text=f"Buy {entity[3]}", callback_data=f'buy{product}'))
	keyboard.add(types.InlineKeyboardButton(text="Back", callback_data='back'))
	bot.send_photo(chat_id=chat.id, photo=open(entity[1], 'rb'), caption=entity[2], reply_markup=keyboard)


def buy_product(call):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{call.from_user.id}'""").fetchall()[0][1]
	price = cursor.execute(f"""SELECT * FROM shop WHERE name = '{call.data[3:]}'""").fetchall()[0][3]
	if balance >= price:
		cursor.execute(f"""UPDATE wallet SET balance = {balance - price} WHERE telegram_id = {call.from_user.id}""")
		conn.commit()
		bot.send_message(call.message.chat.id, f"Grats. You bought! {call.data[3:]}")
	else:
		bot.send_message(call.message.chat.id, "Sorry, you don't have enough money.")
		time.sleep(2)
		# order(call)
		bot.send_message(call.message.chat.id, "Do you need job?")


# def order(call):
# 	keyboard = types.InlineKeyboardMarkup()
# 	keyboard.row(types.InlineKeyboardButton(text="Yes", callback_data="Yes"),
# 				 types.InlineKeyboardButton(text="No", callback_data="No"))
# 	bot.send_message(call.message.chat.id, f"Do you want to make money?", reply_markup=keyboard)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def quest1(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{message.from_user.id}'""").fetchall()[0][1]
	chat_id = message.chat.id
	if message.text == 'Yes' or 'yes' or 'yep':
		if balance == 0:
			bot.register_next_step_handler(bot.send_message(message.chat.id, 'It is your first task'), quest1)
		elif balance == 2500:
			bot.register_next_step_handler(bot.send_message(chat_id, "It is your second task"), quest2)
		elif balance == 5500:
			bot.register_next_step_handler(bot.send_message(chat_id, "It is your last task"), quest3)
	else:
		bot.send_message(chat_id, "You already done all job")

def quest1(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{message.from_user.id}'""").fetchall()[0][1]
	text = message.text
	chat_id = message.chat.id
	if text == "Answer1":
		time.sleep(3)
		cursor.execute(f"""UPDATE wallet SET balance = {balance + 2500} WHERE telegram_id = {message.from_user.id}""")
		conn.commit()
		msg =
		bot.register_next_step_handler(bot.send_message(chat_id, f"Well done, take 2500$ \nThis is the second task:"), quest2)
	else:
		message = bot.send_message(chat_id, 'It\'s wrong. Come back when you finish task')
		bot.register_next_step_handler(message, quest1)
		return

def quest2(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{message.from_user.id}'""").fetchall()[0][1]
	text = message.text
	chat_id = message.chat.id
	if text == "Answer2":
		time.sleep(3)
		cursor.execute(f"""UPDATE wallet SET balance = {balance + 3000} WHERE telegram_id = {message.from_user.id}""")
		conn.commit()
		bot.register_next_step_handler(bot.send_message(chat_id, f"Well done, take 3000$ \nThis is the last task:"), quest3)
	else:
		message = bot.send_message(chat_id, 'It\'s wrong. Come back when you finish task')
		bot.register_next_step_handler(message, quest1)
		return

def quest3(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{message.from_user.id}'""").fetchall()[0][1]
	text = message.text
	chat_id = message.chat.id
	if text == "Answer3":
		time.sleep(3)
		cursor.execute(f"""UPDATE wallet SET balance = {balance + 3500} WHERE telegram_id = {message.from_user.id}""")
		conn.commit()
		bot.register_next_step_handler(bot.send_message(chat_id, f"I havent any work for you. You can \\start trading"), quest1)
	else:
		message = bot.send_message(chat_id, 'It\'s wrong. Come back when you finish task')
		bot.register_next_step_handler(message, quest1)
		return

# def job(call):
# 	conn = sqlite3.connect("mydatabase.db")
# 	cursor = conn.cursor()
# 	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{call.from_user.id}'""").fetchall()[0][1]
#
# def quest3(message):
# 	conn = sqlite3.connect("mydatabase.db")
# 	cursor = conn.cursor()
# 	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{message.from_user.id}'""").fetchall()[0][1]
# 	text = message.text
# 	chat_id = message.chat.id
# 	if text == "Answer1":
# 		time.sleep(3)
# 		bot.send_message(chat_id, f"Well done, take 2500$")
# 		cursor.execute(f"""UPDATE wallet SET balance = {balance + 2500} WHERE telegram_id = {message.from_user.id}""")
# 		conn.commit()
# 	else:
# 		message = bot.send_message(chat_id, 'It\'s wrong. Come back when you finish task')
# 		bot.register_next_step_handler(message, quest1)
# 		return

# def job2(call):
# 	conn = sqlite3.connect("mydatabase.db")
# 	cursor = conn.cursor()
# 	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{call.from_user.id}'""").fetchall()[0][1]
# 	bot.send_message(call.message.chat.id, f"Second quest")
# 	@bot.message_handler(func=lambda message: True, content_types=['text'])
# 	def second_quest(message):
# 		if message.text == "Answer2":
# 			time.sleep(3)
# 			bot.send_message(call.message.chat.id, f"Well done, take 3000$")
# 			cursor.execute(f"""UPDATE wallet SET balance = {balance + 3000} WHERE telegram_id = {call.from_user.id}""")
# 			conn.commit()
# 		else:
# 			bot.send_message(call.message.chat.id, f"Wrong answer 2!")
#
# def job3(call):
# 	conn = sqlite3.connect("mydatabase.db")
# 	cursor = conn.cursor()
# 	balance = cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = '{call.from_user.id}'""").fetchall()[0][1]
# 	bot.send_message(call.message.chat.id, f"Third quest")
# 	@bot.message_handler(func=lambda message: True, content_types=['text'])
# 	def third_quest(message):
# 		if message.text == "Answer3":
# 			time.sleep(3)
# 			bot.send_message(call.message.chat.id, f"Well done, take 3500$")
# 			cursor.execute(f"""UPDATE wallet SET balance = {balance + 3500} WHERE telegram_id = {call.from_user.id}""")
# 			conn.commit()
# 		else:
# 			bot.send_message(call.message.chat.id, f"Wrong answer 3!")

# @bot.message_handler(func=lambda message: message.text == 'I want to make money')
# def quest1(message):
# 	# conn = sqlite3.connect("mydatabase.db")
# 	# cursor = conn.cursor()
# 	# balance = 0
# 	if balance == 0:
# 		bot.send_message(message.chat.id, 'Task1')
# 		bot
# 	elif balance == 2500:
# 		bot.send_message(message.chat.id, 'Task2')
# 	elif balance == 5500:
# 		bot.send_message(message.chat.id, 'Task3')

init()
bot.polling()
