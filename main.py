from typing import List
import requests, telebot, sqlite3
import os, threading, schedule
import logging
from datetime import datetime
from telebot import types
from config import bot_token, website_links, admin_users, def_schedule

# CONFIGURATION
logging.basicConfig(
    filename="main.log", 
    format='%(asctime)s [%(levelname)s]: %(message)s',
    level=logging.INFO, 
    datefmt='%d-%b-%y %H:%M:%S'
)

command_names = {
    'get_users': '🗒\nList users',
    'add_user': '🍥\nAdd user',
    'del_user': '🗑\nDel user',

    'get_info': 'ℹ️\nGet info',
    'edit_links': '🌐\nEdit links',
    'edit_schedule': '📅\nEdit schedule',
}

def sql_fetch_query(query_req: str) -> list:

    with sqlite3.connect('bot.db') as conn:
        cursor = conn.cursor()
        return cursor.execute(query_req).fetchall()

def sql_exec_query(query_req: str) -> None:

    with sqlite3.connect('bot.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query_req)

# CONNECTIONS
logging.info('')
logging.info('Bot started: Looking for a .db file')

if os.path.isfile('bot.db'):
    
    logging.info('Found bot.db, connecting')
    try:
        query_output = sql_fetch_query("""SELECT t_id FROM users WHERE admin = 1;""")
        for entry in query_output:
            admin_users.append(entry[0])
    except Exception as e:
        logging.critical(f'DB ERROR {e}')
    finally:
        logging.info('Connected to the bot.db')
    
else: # Create new db if no db exists
    logging.info('Did not found .db file, creating new bot.db file')
    
    try:
        sql_exec_query('''CREATE TABLE users (
                            id INTEGER PRIMARY KEY,
                            t_id INTEGER NOT NULL UNIQUE,
                            name TEXT NOT NULL,
                            admin BOOL DEFAULT 0);''')

        sql_exec_query('''CREATE TABLE links (
                            id INTEGER PRIMARY KEY,
                            link TEXT NOT NULL);''')

        sql_exec_query('''CREATE TABLE schedule (
                            id INTEGER PRIMARY KEY,
                            minutes INTEGER NOT NULL);''')

        sql_exec_query(f'''INSERT INTO schedule (minutes) VALUES ({def_schedule})''')

        for link in website_links:
            sql_exec_query(f'''INSERT INTO links (link) VALUES ('{link}')''')

    except Exception as e:
        logging.critical(f'DB ERROR {e}')
    finally:
        logging.info('Created bot.db')

bot = telebot.TeleBot(bot_token, parse_mode='html')

# MESSAGE HANDLERS
@bot.message_handler(commands=['start'], func=lambda msg: msg.from_user.id in admin_users)
def start_message(msg):
    logging.info(f'USER START [{msg.from_user.id}] {msg.from_user.username}')
    markup = types.ReplyKeyboardMarkup(row_width=3)
    markup.add(
        types.KeyboardButton(command_names['get_users']),
        types.KeyboardButton(command_names['add_user']),
        types.KeyboardButton(command_names['del_user']),

        types.KeyboardButton(command_names['get_info']),
        types.KeyboardButton(command_names['edit_links']),
        #types.KeyboardButton(command_names['edit_schedule']),
    )

    bot.reply_to(msg, 'Got you admin 😉', reply_markup=markup)


###### GET USERS ######
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
                                        and msg.content_type == 'text' \
                                        and msg.text == command_names['get_users'])
def getusers(msg):
    logging.info(f'GETUSERS by: [{msg.from_user.id}] {msg.from_user.username} {msg.from_user.first_name} {msg.from_user.last_name}')

    out_msg = "# |  ID  | NAME | ADMIN \n"
    query_output = sql_fetch_query("""SELECT * FROM users""")

    for row in query_output:
        out_msg += str(row[0]) + " | " + str(row[1])  + " | " + row[2] + " | " + str(row[3]) + "\n"

    bot.reply_to(msg, out_msg)


###### GET INFO ######
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
                                        and msg.content_type == 'text' \
                                        and msg.text == command_names['get_info'])
def getinfo(msg):
    logging.info(f'GETINFO by: [{msg.from_user.id}] {msg.from_user.username} {msg.from_user.first_name} {msg.from_user.last_name}')

    schedule = sql_fetch_query('''SELECT minutes FROM schedule''')
    links = sql_fetch_query('''SELECT link FROM links''')
    links_text = ''
    for link in links:
        links_text += f'\t\t\t{link[0]}\n'

    # Website links

    bot.reply_to(msg, f"Schedule time: <b>every {schedule[0][0]} minutes</b> \nWebsite links: \n{links_text}")


###### ADD USER ######
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
                                        and msg.content_type == 'text' \
                                        and msg.text == command_names['add_user'])
def pre_adduser(msg):
    logging.info(f'ADDUSER INIT by: [{msg.from_user.id}] {msg.from_user.username}')
    bot_reply = bot.send_message( msg.chat.id, 
        '🍥🍥🍥 ADD USER 🍥🍥🍥\nPlease send the message in the next format:\
            \nGet your id here: @userinfobot \n\n[user_id] [user_name] [admin(0 or 1)]\nexample: 12345 bob 0',        
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

        sql_exec_query(f"""INSERT INTO users
                            (t_id, name, admin) 
                            VALUES 
                            ({split_msg[0]}, "{split_msg[1]}", {split_msg[2]})""")

        bot.send_message(msg.chat.id, f"User {split_msg[1]} added to the list!")
    
        # Append new admin to the admin_users list
        if int(split_msg[2]) == 1:
            admin_users.append(int(split_msg[0]))

        logging.info(f'ADDUSER DONE ({split_msg[0]} {split_msg[1]} {split_msg[2]})')
    except Exception as e:
        bot.send_message(msg.chat.id, f"Error: \n{e}")
        logging.info(f'ADDUSER FAILED')
        logging.warning(e)


###### DEL USER ######
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
                                        and msg.content_type == 'text' \
                                        and msg.text == command_names['del_user'])
def pre_deluser(msg):
    logging.info(f'DELUSER INIT by: [{msg.from_user.id}] {msg.from_user.username}')
    bot_reply = bot.send_message(msg.chat.id, '🗑🗑🗑 DEL USER 🗑🗑🗑\nPlease send the message in the next format: \n\n[user_id]')
    bot.register_next_step_handler(bot_reply, post_deluser)

def post_deluser(msg):
    try:
        try:
            user_id = int(msg.text)
        except:
            bot.reply_to(msg, 'Cannot convert this to an id')
            return

        # Remove user from admin_users
        getuser_query = sql_fetch_query(f"""SELECT admin, name FROM users WHERE t_id = {user_id};""")
        if getuser_query[0][0] == 1:
            admin_users.pop(admin_users.index(user_id))

        sql_exec_query(f"""DELETE FROM users
                            WHERE t_id = {user_id};""")

        bot.send_message(msg.chat.id, f"User with id: {user_id} removed!")
        logging.info(f'DELUSER DONE ({user_id} {getuser_query[0][1]})')

    except Exception as e:
        bot.send_message(msg.chat.id, f"Error: \n{str(e)}")
        logging.info(f'DELUSER FAILED')

###### EDIT LINKS ######
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
                                        and msg.content_type == 'text' \
                                        and msg.text == command_names['edit_links'])
def pre_editlinks(msg):
    logging.info(f'EDIT LINKS by: [{msg.from_user.id}] {msg.from_user.username}')
    bot_reply = bot.reply_to(msg, 'Send list of links you want to monitor in this format: \n\nlink1\nlink2\nlink3 \n\nSend /cancel to abort')
    bot.register_next_step_handler(bot_reply, post_editlinks)

def post_editlinks(msg):
    if msg.text.strip() == '/cancel':
        bot.reply_to(msg, 'Edit canceled')
        return

    links = msg.text.split('\n')
    links = [link.strip() for link in links]
    
    links_query = ""
    for i, link in enumerate(links):
        if i == len(links)-1:
            links_query += f"('{link}');"
        else:
            links_query += f"('{link}'), "

    sql_exec_query('''DELETE FROM links''')
    query_msg = f'''INSERT INTO links (link) VALUES {links_query}'''
    sql_exec_query(query_msg)
    bot.reply_to(msg, 'Links updated...')


# ###### EDIT SCHEDULE ######
# @bot.message_handler(func=lambda msg: msg.from_user.id in admin_users \
#                                         and msg.content_type == 'text' \
#                                         and msg.text == command_names['edit_schedule'])
# def pre_editschedule(msg):
#     logging.info(f'EDIT SCHEDULE by: [{msg.from_user.id}] {msg.from_user.username}')
#     bot_reply = bot.reply_to(msg, 'Send new schedule in minutes (number up to 60): \n\nSend /cancel to abort')
#     bot.register_next_step_handler(bot_reply, post_editschedule)

# def post_editschedule(msg):
#     if msg.text.strip() == '/cancel':
#         bot.reply_to(msg, 'Edit canceled')
#         return 

#     try:
#         if int(msg.text) > 0 and int(msg.text) <= 60:
#             sql_exec_query('''DELETE FROM schedule''')
#             sql_exec_query(f'''INSERT INTO schedule (minutes) VALUES ({int(msg.text)})''')
#             bot.reply_to(msg, 'Schedule updated...')
#         else:
#             bot.reply_to(msg, 'Value is not integer or not in range of 0 to 60 minutes')
#     except Exception as e:
#         bot.reply_to(msg, f'Exception: {str(e)}')

# BOT PING 
def test_sites(ping_time):

    def ping(ping_time):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        getuser_query = sql_fetch_query("""SELECT t_id FROM users;""")

        logging.info('')
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
        logging.info('')

    schedule.every(ping_time).minutes.do(ping, ping_time)
    while True:
        schedule.run_pending()

# PING FUNCTION THREAD
chedule_tile = sql_fetch_query('''SELECT minutes FROM schedule''')
ping_thread = threading.Thread(target=test_sites, args=(chedule_tile[0][0], ))
ping_thread.start()
logging.info('Started ping schedule')

bot.polling()