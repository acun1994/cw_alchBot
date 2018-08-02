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
import re

# DEV : Replace this if using heroku
#token = os.environ["TELEGRAM_TOKEN"]
f = open("token", "r")
if f.mode == "r":
    token = f.read()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

errorCount = 0
proccessCount = 0

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
            global errorCount 
            errorCount = errorCount + 1

            firstname = "Bot"   
            username = "-"
            text = "None"
            if update and update.message  :
                update.message.reply_text("Sorry, I have encountered an error. My master has been informed. Please use /help for more information")
                firstname = update.message.from_user.first_name
                text = update.message.text
                if update.message.from_user.username:
                    username = update.message.from_user.username

            template = "CW - ERROR \nUser: {2} ({3})\nAn exception of type {0} occurred\nArguments:\n{1!r}\nText :\n{4}"
            message = template.format(type(e).__name__, e.args, firstname, username, text)
            bot.send_message(chat_id='-1001213337130',
                             text=message, parse_mode = ParseMode.HTML)
    return wrap

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
@catch_error
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Bot Name : `CW (EU) Guild Inventory Helper`\n\
Developer : @acun1994\n\
Special Thanks: @wolvix and @Knightniwrem for breaking the bot\n\
Description : \n\
Bot that assists in guild inventory management (Deposit, Withdraw)\n\
Use /help for more info', parse_mode=ParseMode.MARKDOWN)

@catch_error
def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('INLINE Bot usage: \n@cw_guildBot {itemName} {quantity} {"w" (optional, to withdraw)}. \n\nItem Name does not have to be full, 3 characters is enough.\n\
    STANDARD Bot usage: \nForward a list of items. Should support all inventories.\n\
    RECIPE Bot usage: \nForward the recipe text as received from CW.\
    WARNING: Enchanted and unique items will NOT be processed\n\
    Poke @acun1994 if you find something that isn\'t handled yet')

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
        bot.sendMessage(chat_id='-1001213337130', text = 'CW - <b>Telegram Error</b>\n Update "{}" caused error "{}"'.format(update, context), parse_mode = "HTML")
        return
    except Exception:
        logger.warning('Update "%s" caused error "%s"', update, context)
        bot.sendMessage(chat_id='-1001213337130', text = 'CW - <b>Error</b>\n Update "{}" caused error "{}"'.format(update, context), parse_mode = "HTML")

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
