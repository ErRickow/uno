# UNO Bot

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](./LICENSE)

Telegram Bot that allows you to play the popular card game UNO via inline queries. The bot currently runs as [@unobot](http://telegram.me/unobot)

To run the bot yourself, you will need: 
- Python (tested with 3.4 and 3.5)
- The [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) module version 5.0.0
- [Pony ORM](https://ponyorm.com/)

## Setup
- Get a bot token from [@BotFather](http://telegram.me/BotFather) and place it in `credentials.py`
- Convert all language files from .po to .mo by executing the bash script 'compile.sh' located in the locales folder
- Use `/setinline` and `/setinlinefeedback` with BotFather for your bot

Then run the bot with `python3 bot.py`

Code documentation is minimal but there
