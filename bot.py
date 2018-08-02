# DEF : Imports
import os, logging
from uuid import uuid4

from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import escape_markdown
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                            TimedOut, ChatMigrated, NetworkError)

from functools import wraps
from datetime import datetime
import pyrebase

# DEV : Replace this if using heroku
#token = os.environ["TELEGRAM_TOKEN"]
f = open("token", "r")
if f.mode == "r":
    token = f.read()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

#Firebase config
config = {
  "apiKey": "AIzaSyDNsScR8JpErWjVxU3oUr3Th0GRGSW5GXA",
  "authDomain": "chat-wars-bots.firebaseapp.com",
  "databaseURL": "https://chat-wars-bots.firebaseio.com",
  "storageBucket": "chat-wars-bots.appspot.com",
  "serviceAccount": "chat-wars-bots-a847acf4208f.json"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
potions = db.child("potions").get()
print("Ready")

def catch_error(f):
    @wraps(f)
    def wrap(bot, update, context = ""):
        try:
            return f(bot, update)
        except IndexError as e:
            if update and update.message  :
                update.message.reply_text("No transferrable items found")
        except Exception as e:
            logger.error(str(e))

            firstname = "Bot"   
            username = "-"
            text = "None"
            if update and update.message  :
                update.message.reply_text("Sorry, I have encountered an error. My master has been informed. Please use /help for more information")
                firstname = update.message.from_user.first_name
                text = update.message.text
                if update.message.from_user.username:
                    username = update.message.from_user.username

            template = "CW Alch - ERROR \nUser: {2} ({3})\nAn exception of type {0} occurred\nArguments:\n{1!r}\nText :\n{4}"
            message = template.format(type(e).__name__, e.args, firstname, username, text)
            bot.send_message(chat_id='-1001213337130',
                             text=message, parse_mode = ParseMode.HTML)
    return wrap

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
@catch_error
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Bot Name : `CW (EU) Alchemist Bot`\n\
Developer : @acun1994\n\
Special Thanks: @morth for the incredible work done on the original\n\
Description : \n\
Bot that assists in potion brewing\n\
Use /help for more info', parse_mode=ParseMode.MARKDOWN)

@catch_error
def dump(bot,update):
    text = ""
    print("Start")
    for potion in potions.each():
        print(potion.key())
        text = potion.key() + " (" + potion.val()['id'] + ") " + str(potion.val()['mana']) + "💧"
        for ing,amt in potion.val()['mats'].items():
            text += "\n" + ing + " x" + str(amt)
        update.message.reply_text(text)

@catch_error
def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Forward your /alch here. The bot will reply with a list of craftable potions/ingredients\nPoke @acun1994 if it breaks')

@catch_error
def error(bot, update, context = ""):
    """Log Errors caused by Updates."""
    if update is None: return
    
    try:
        raise context
    except BadRequest:
        return
    except TimedOut:
        return
    except TelegramError:
        logger.warning('Update "%s" caused error "%s"', update, context)
        return
    except Exception:
        logger.warning('Update "%s" caused error "%s"', update, context)

# Create the Updater and pass it your bot's token.
# Make sure to set use_context=True to use the new context baspls ed callbacks
# Post version 12 this will no longer be necessary
updater = Updater(token)
jobQ = updater.job_queue

# Get the dispatcher to register handlers
dp = updater.dispatcher

# on different commands - answer in Telegram
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help))
dp.add_handler(CommandHandler("dump", dump))

# Schedule
#jobQ.run_repeating(status, interval=60, first = 0)

# on noncommand i.e message - echo the message on Telegram
#dp.add_handler(MessageHandler(Filters.text, process))

# log all errors
dp.add_error_handler(error)

# Start the Bot
updater.start_polling(clean = True)

# Block until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.
updater.idle()
