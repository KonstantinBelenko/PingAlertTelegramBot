import telebot, sqlite3, os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot_token, admin_users

# CONNECTIONS
if os.path.isfile('users.db'):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    print("Conne    cted to the user.db")
else: # Create new db if no db exists
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    create_table_query = '''CREATE TABLE users (
                        id INTEGER PRIMARY KEY,
                        t_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        admin BOOL DEFAULT 0);'''
    cursor.execute(create_table_query)
    conn.commit()
    print('Created new users.db')

bot = telebot.TeleBot(bot_token, parse_mode=None)

# Message hadnlers

@bot.message_handler(comands=['start'], func=lambda msg: msg.from_user.id in admin_users)
def start_message():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1

@bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
                                  and msg.content_type == 'text' \
                                  and msg.text == 'getusers')
def getusers(msg):
    bot.reply_to(msg, 'nioce')


bot.polling()
conn.close()
