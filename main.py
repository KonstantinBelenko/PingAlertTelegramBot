import requests
import telebot
from datetime import datetime
from config import bot_token, users, website_link

bot = telebot.TeleBot(bot_token, parse_mode=None)

for user in users:
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    
    try:
        r = requests.get(website_link)
        print(current_time + ": " + str(r.status_code) + "\n")
    except Exception as e:
        msg = f"!!!WARNING!!! \n{website_link} does not respond! \nError: " + str(e) + " \n\n" + current_time
        print(current_time + ": ERROR: " + str(e) "\n")
        bot.send_message(user, msg)
    
    bot.stop_polling()

bot.polling()
