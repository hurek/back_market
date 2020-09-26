import sqlite3
import telebot
import time
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
		cursor.execute(f"""INSERT INTO wallet ('telegram_id', 'username') VALUES ('{message.from_user.id}', '{message.from_user.username}')""")
		cursor.execute(f"""INSERT INTO steps ('telegram_id', 'username') VALUES ('{message.from_user.id}', '{message.from_user.username}')""")
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
	balance = cursor.execute(f"SELECT * FROM wallet WHERE telegram_id = '{call.from_user.id}'").fetchall()[0][2]
	price = cursor.execute(f"SELECT * FROM shop WHERE name = '{call.data[3:]}'").fetchall()[0][3]
	if balance >= price:
		cursor.execute(f"""UPDATE wallet SET balance = {balance - price} WHERE telegram_id = {call.from_user.id}""")
		conn.commit()
		conn.close()
		bot.send_message(call.message.chat.id, f"Grats. You bought {call.data[3:]}!\nYour order number:\n3cb50a7b990798c0559b9032b5f8586f7de223217528591d6f3dce959180038b")
	else:
		conn.close()
		bot.send_message(call.message.chat.id, "Sorry, you don't have enough money.")
		time.sleep(2)
		bot.send_message(call.message.chat.id, "If you need money, I have an offer for you. Write me /job and I'll tell you more.")

@bot.message_handler(commands=['job'])
def job(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	task = {
		1: {'text': "This is your first task:\nhttps://imgur.com/a/IuepuX6\nIn addition to selling unusual items, I also do detective work.\nOne of my clients asked me to decipher it.\nSend me an answer when you're done.",'answer': "minimumstakeamount"},
		2: {'text': "This is your second task:\nhttps://pastebin.com/MjfZN9t5\nAnother client encrypted the password to his bank account and forgot how to decrypt it.\nHe pays a lot of money for decryption. I'll wait for the password from the bank.",'answer': "1c62590c99871030411c60c4780da31ec05c4db349e2f02d79c01228fccd9380"},
		3: {'text': "This is your third task:\n((BV80605001911AP)- (sqrt(-1)))^2\nAnd finally the last task. To be honest, I'm ashamed to ask you, but could you help with my child's homework?\nI've seen this problem somewhere, but I can't remember the solution.\nI'll wait for the number.",'answer': "-16"}}
	if not cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = {message.from_user.id}""").fetchall():
		cursor.execute(f"""INSERT INTO wallet ('telegram_id', 'username') VALUES ('{message.from_user.id}', '{message.from_user.username}')""")
		cursor.execute(f"""INSERT INTO steps ('telegram_id', 'username') VALUES ('{message.from_user.id}', '{message.from_user.username}')""")
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
		bot.send_message(message.chat.id, 'You already solved all my tasks! You can start trading now')
	conn.close()


@bot.message_handler(func=lambda message: True, content_types=['text'])
def quest(message):
	conn = sqlite3.connect("mydatabase.db")
	cursor = conn.cursor()
	task = {
		1: {'text': "This is your first task:\nhttps://imgur.com/a/IuepuX6\nIn addition to selling unusual items, I also do detective work.\nOne of my clients asked me to decipher it.\nSend me an answer when you're done.",'answer': "minimumstakeamount"},
		2: {'text': "This is your second task:\nhttps://pastebin.com/MjfZN9t5\nAnother client encrypted the password to his bank account and forgot how to decrypt it.\nHe pays a lot of money for decryption. I'll wait for the password from the bank.",'answer': "1c62590c99871030411c60c4780da31ec05c4db349e2f02d79c01228fccd9380"},
		3: {'text': "This is your third task:\n((BV80605001911AP)- (sqrt(-1)))^2\nAnd finally the last task. To be honest, I'm ashamed to ask you, but could you help with my child's homework?\nI've seen this problem somewhere, but I can't remember the solution.\nI'll wait for the number.",'answer': "-16"}}
	if not cursor.execute(f"""SELECT * FROM wallet WHERE telegram_id = {message.from_user.id}""").fetchall():
		cursor.execute(f"""INSERT INTO wallet ('telegram_id', 'username') VALUES ('{message.from_user.id}', '{message.from_user.username}')""")
		cursor.execute(f"""INSERT INTO steps ('telegram_id', 'username') VALUES ('{message.from_user.id}', '{message.from_user.username}')""")
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
			bot.send_message(message.chat.id, 'Well done! Take 3000$ Write me /job to get the next task.')
		else:
			bot.send_message(message.chat.id, 'Wrong answer! I\'m waiting for right answer.')
	elif step == 'second':
		if message.text == task[2]['answer']:
			bd_change(f"""UPDATE steps SET step = 'third' WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE steps SET status = 'wait' WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE wallet SET balance = 6000 WHERE telegram_id = {message.from_user.id}""")
			bot.send_message(message.chat.id, 'Well done! Take 3000$ Write me /job to get the next task.')
		else:
			bot.send_message(message.chat.id, 'Wrong answer! I\'m waiting for right answer.')
	elif step == 'third':
		if message.text == task[3]['answer']:
			bd_change(f"""UPDATE steps SET step = 'passed' WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE wallet SET balance = 9000 WHERE telegram_id = {message.from_user.id}""")
			bd_change(f"""UPDATE steps SET status = 'wait' WHERE telegram_id = {message.from_user.id}""")
			bot.send_message(message.chat.id, 'Well done! Take 3000$ You\'re good! You completed all my tasks. You can start trading.')
			send_welcome(message)
		else:
			bot.send_message(message.chat.id, 'Wrong answer! I\'m waiting for right answer.')
	else:
		pass
	conn.commit()
	conn.close()

init()
bot.polling()
