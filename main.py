import requests, telebot, sqlite3
import os, threading, schedule
import logging
from datetime import datetime
from telebot import types
from config import bot_token, website_links, admin_users

# LOGGING CONFIGURATION
logging.basicConfig(
    filename="main.log", 
    format='%(asctime)s [%(levelname)s]: %(message)s',
    level=logging.INFO, 
    datefmt='%d-%b-%y %H:%M:%S'
)

# CONNECTIONS\
logging.info('')
logging.info('Looking for a .db file')
if os.path.isfile('users.db'):
    logging.info('Found users.db, connecting')

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        query_output = cursor.execute("""SELECT t_id FROM users WHERE admin = 1;""").fetchall()
        for entry in query_output:
            admin_users.append(entry[0])

    except Exception as e:
        logging.critical(f'DB ERROR {e}')
    finally:
        logging.info('Connected to the users.db')
    
else: # Create new db if no db exists
    logging.info('Did not found .db file, creating new users.db file')
    
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        create_table_query = '''CREATE TABLE users (
                            id INTEGER PRIMARY KEY,
                            t_id INTEGER NOT NULL UNIQUE,
                            name TEXT NOT NULL,
                            admin BOOL DEFAULT 0);'''
        cursor.execute(create_table_query)
    except Exception as e:
        logging.critical(f'DB ERROR {e}')
    finally:
        logging.info('Created users.db')

cursor.close()
conn.commit()

bot = telebot.TeleBot(bot_token, parse_mode=None)

# MESSAGE HANDLERS

@bot.message_handler(commands=['start'], func=lambda msg: msg.from_user.id in admin_users)
def start_message(msg):
    logging.info(f'USER START [{msg.from_user.id}] {msg.from_user.username}')
    markup = types.ReplyKeyboardMarkup(row_width=1)
    markup.add(
        types.KeyboardButton('🔎 get users'),
        types.KeyboardButton('🍥 add user'),
        types.KeyboardButton('🗑 del user'),
    )

    bot.reply_to(msg, 'Got you admin 😉', reply_markup=markup)


###### GET USERS ######
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
                                        and msg.content_type == 'text' \
                                        and msg.text == '🔎 get users')
def getusers(msg):
    print(msg.from_user)
    logging.info(f'USER GETUSERS [{msg.from_user.id}] {msg.from_user.username} {msg.from_user.first_name} {msg.from_user.last_name}')
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query_output = cursor.execute("""SELECT * FROM users""").fetchall()

    out_msg = "# |  ID  | NAME | ADMIN \n"
    for row in query_output:
        out_msg += str(row[0]) + " | " + str(row[1])  + " | " + row[2] + " | " + str(row[3]) + "\n"

    bot.reply_to(msg, out_msg)

    cursor.close()
    conn.commit()


###### ADD USER ######
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
                                        and msg.content_type == 'text' \
                                        and msg.text == '🍥 add user')
def pre_adduser(msg):
    logging.info(f'USER ADDUSER [{msg.from_user.id}] {msg.from_user.username}')
    bot_reply = bot.send_message(
        msg.chat.id, 
        '🍥🍥🍥 ADD USER 🍥🍥🍥\nPlease send the message in the next format:\
            \nGet your id here: @userinfobot \n\n<user_id> <user_name> <admin(0 or 1)>',        
    )

    bot.register_next_step_handler(bot_reply, post_adduser)

def post_adduser(msg):
    split_msg = msg.text.split(' ')
    if len(split_msg) != 3:
        bot.send_message(msg.chat.id, "Wrong message format!")
        return

    try:

        if int(split_msg[2]) > 1 or int(split_msg[2]) < 0:
            bot.send_message(msg.chat.id, "Wrong admin type!")
            return

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        adduser_query = f"""INSERT INTO users
                            (t_id, name, admin) 
                            VALUES 
                            ({split_msg[0]}, "{split_msg[1]}", {split_msg[2]})"""

        cursor.execute(adduser_query)
        cursor.close()
        conn.commit()

        bot.send_message(msg.chat.id, f"User {split_msg[1]} added to the list!")
    
        # Append new admin to the admin_users list
        if int(split_msg[2]) == 1:
            admin_users.append(int(split_msg[0]))

        logging.info(f'Added new user ({split_msg[0]}) {split_msg[1]} {split_msg[2]}')
    except Exception as e:
        bot.send_message(msg.chat.id, f"Error: \n{e}")
        logging.info(f'Add new user FAILED')
        logging.warning(e)


###### DEL USER ######
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
                                        and msg.content_type == 'text' \
                                        and msg.text == '🗑 del user')
def pre_deluser(msg):
    logging.info(f'USER DELUSER [{msg.from_user.id}] {msg.from_user.username}')
    bot_reply = bot.send_message(msg.chat.id, '🗑🗑🗑 DEL USER 🗑🗑🗑\nPlease send the message in the next format: \n\n <user_id>')
    bot.register_next_step_handler(bot_reply, post_deluser)

def post_deluser(msg):
    try:
        user_id = int(msg.text)
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        getuser_query = cursor.execute(f"""SELECT admin, name FROM users WHERE t_id = {user_id};""").fetchall()
        
        # Remove user from admin_users
        if getuser_query[0][0] == 1:
            admin_users.pop(admin_users.index(user_id))

        deluser_query = f"""DELETE FROM users
                            WHERE t_id = {user_id};"""

        cursor.execute(deluser_query)
        cursor.close()
        conn.commit()

        bot.send_message(msg.chat.id, f"User with id: {user_id} removed!")
        logging.info(f'Removed user ({user_id}) {getuser_query[0][1]}')

    except Exception as e:
        bot.send_message(msg.chat.id, f"Error: \n{e}")
        logging.info(f'Removed user FAILED')
        logging.warning(e)

# BOT PING 

# @bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
#                                         and msg.content_type == 'text' \
#                                         and msg.text == 'test')

def test_sites():

    def ping():
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        getuser_query = cursor.execute(f"""SELECT t_id FROM users;""").fetchall()

        logging.info('PINGING WEBSITES START')
        
        for site_url in website_links:

            try: # We use `try` here because if site does not respond - request module will call an exception

                r = requests.get(site_url)   
                logging.info(f'{site_url} OKAY')         
                logging.info(f'STATUS CODE: {str(r.status_code)}')    
            
            except Exception as e:
                logging.info(f'{site_url} ERROR')         
                logging.info(f'STATUS CODE: {str(e)}')

                for user in getuser_query:
                    user_id = user[0] # we select user id from user[0] because sql query returns a tuple like this (id, )

                    try:
                        bot.send_message(user_id, f"{site_url} does not respond! \nPing response: {str(e)} \n\nTime: {current_time}")
                    except:
                        logging.warning(f'USER ID [{user_id}] is wrong')

        logging.info('PINGING WEBSITES END')

    schedule.every(1).minutes.do(ping)
    while True:
        schedule.run_pending()

# PING FUNCTION THREAD
ping_thread = threading.Thread(target=test_sites)
ping_thread.start()
logging.info('Started ping schedule')

bot.polling()