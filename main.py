import requests
import telebot
from datetime import datetime
from config import bot_token, users, website_links

bot = telebot.TeleBot(bot_token, parse_mode=None)

now = datetime.now()
current_time = now.strftime("%H:%M:%S")

print(f"{current_time} [[[\n")
# List each specified website url
for site_url in website_links:

    try:
        # Ping the website
        r = requests.get(site_url)
        
        # Print out logs
        print(f"{site_url} OK! \nStatus code: {str(r.status_code)} \nTime: {current_time}\n")
    
    except Exception as e:
        
        # Print out logs
        print(f"{site_url} does not respond! \nError: {str(e)} \nTime: {current_time}\n")
        
        for user in users:
            # Send telegram warning
            bot.send_message(user, f"{site_url} does not respond! \nPing response: {str(e)} \n\nTime: {current_time}")

# End the broadcast
bot.stop_polling()

print("]]]\n")

bot.polling()
