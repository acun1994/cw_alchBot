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
  "serviceAccount": "serviceToken.json"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
potions = db.child("potions").get()
items = db.child("items").get()

itemCodes = {}

for item in items.each():
   itemCodes[item.key()] = item.val()["id"]
print("Ready for processing")

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

@catch_error
def inlinequery(bot, update):
    """Handle the inline query."""
    query = update.inline_query.query

    results = []

    if query == '' or len(query) < 3:
        update.inline_query.answer(results)
        return

    listValid = [key for key, value in potions.val().items() if query in key.lower()]

    if len(listValid) == 0:
        results = [
            InlineQueryResultArticle(
                id=uuid4(),
                title = "Not Found",
                input_message_content = InputTextMessageContent(
                    '{} not found'.format(" ".join(query))
                )
            )
        ]

    else:
        for key in listValid: 
            curPotion = potions.val()[key]
            ingList = ""
            for k,v in curPotion['mats'].items():
                if ingList is not "": ingList += ", "
                ingList += k + " x" + str(v)

            results.append(
                InlineQueryResultArticle(
                    id=uuid4(),
                    title = "{}".format(key),
                    description = ingList,
                    input_message_content = InputTextMessageContent(
                        "/brew_" + curPotion['id']
                    )
                )
            )

    update.inline_query.answer(results, cache_time = None, is_personal = True)

@catch_error
def process(bot, update):
    #https://t.me/share/url?url=/brew_60%20120 link format for auto forward
    playerInv = update.message.text.splitlines()
    repackPotions = potions.val()

    if "/aa" not in playerInv[1]:
        update.message.reply_text("Please forward me your /alch")

    playerInv = {a[0]:a[1] for a in [line[7:].split(" x ") for line in playerInv[1:]]}

    playerInv = {k.lower(): v for k,v in playerInv.items()}

    craftablePotions = {}

    for k,v in potions.val().items():
        curMats = v['mats']
        craftCount = 0
        try:
            craftCount = min([int(int(playerInv[k.lower()])/v) for k,v in curMats.items()])
        except KeyError:
            craftCount = 0

        craftablePotions[k] = craftCount
    
    replyText = "\n".join(["<a href='https://t.me/share/url?url=/brew_{}%20{}'>{}</a> x {} ( {}💧)".format(repackPotions[k]['id'],v,k,v,v*repackPotions[k]['mana']) for k,v in craftablePotions.items() if v > 0])

    if replyText is None or replyText == "":
        replyText = "You poor thing, you're broke. No brewable items possible"

    update.message.reply_text(replyText, parse_mode="HTML")

@catch_error
def refresh(bot, update):
    global potions
    global itemCodes
    potions = db.child("potions").get()
    update.message.reply_text("Potion List updated!")
    items = db.child("items").get()

    itemCodes.clear()
    for item in items.each():
        itemCodes[item.key()] = item.val()["id"]

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
dp.add_handler(CommandHandler("refresh", refresh))

# Schedule
#jobQ.run_repeating(status, interval=60, first = 0)

# on Inline query
dp.add_handler(InlineQueryHandler(inlinequery))

# on noncommand i.e message - echo the message on Telegram
dp.add_handler(MessageHandler(Filters.text, process))

# log all errors
dp.add_error_handler(error)

# Start the Bot
updater.start_polling(clean = True)

# Block until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.
updater.idle()
