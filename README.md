# What does this project do?
###### !!Warning!! this project uses linux cronjobs as it's schedueling component, so it may differ on other os's

This projects purpose is to provide basic alert and monitoring for your web service. <br>
It uses **python script and a cronjob** as it's way of schedueling and executing tasks <br>

Python script schecks whether specified website responds to the pings and notifies specified users by telegram messanging if something goes wrong. <br>

# How to get it to work?

### 1. Prerequirements

* python3
* pip3
* git

### 2. Install and enable Cron
```
# Insatll Cron
$ sudo apt update && sudo apt install cron

# Enable and start Cron 
$ sudo systemctl enable --now cron

# Check that Cron started 
$ systemctl status cron
```

### 3. Export python script `main.py` into prefered folder / install python dependencies
I will use this path to store python script and cron logs: <br>
`/home/user/python/PingAlertTelegramBot/` <br>
You may change the cronjob string if you change the project path

```
# Create a python folder and enter it
$ cd ~ && mkdir python && cd python 

# Download project repo
$ git clone https://github.com/KonstantinBelenko/PingAlertTelegramBot.git && cd PingAlertTelegramBot

# Install Python dependencies
$ pip3 install -r requirements.txt
```
### 4. Configure the `config.py`
1. Get the bot_token from the **@BotFather**
2. users variable contains ids of users that bot will respond to. You can get your user id from this telegram bot **@userinfobot**.
3. website_link is a link of a web service you want to monitor to.

### 5. Define a cronjob
1. Copy the insides of the `cronjob` file <br>
2. Open cronjobs using preffered editor,  (Here I use vim)
```
$ EDITOR=vim crontab -e
```
3. Press `i` to enter insert mode and press `shift + insert` to paste copied string.
4. You can configure this cronjob schedule using this [article](https://linuxize.com/post/scheduling-cron-jobs-with-crontab/) (It runs the script every 10m by default)
5. Save and exit vim safely by pressing `Esc` and typing `:wq` followed by 'Enter' (use [this article](https://stackoverflow.com/questions/11828270/how-do-i-exit-the-vim-editor) if encounter problems)
6. Restart the cronjob and enjoy your alert bot
`$ sudo systemctl restart cron`
