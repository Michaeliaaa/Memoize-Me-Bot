import logging
from telegram.ext import Updater, InlineQueryHandler, CommandHandler,  CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests
import re
import os
PORT = int(os.environ.get('PORT', 5000))


TOKEN = '1257761341:AAEL0eO8n4kgvSy3CfJgAAg4EkaME4JQ5sM'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text('Type /new to create a new deck of flashcards, /edit to edit an existing deck, or /test to test yourself on an existing deck.')
    
def new(update, context):
    update.message.reply_text('Alright, a new set of flashcards! What are we going to call it?')
    
def add(update, context):
    update.message.reply_text('Let\'s create a new card. First, send me your question. You can type it out or upload a picture!')
    
def delete(update, context):
    update.message.reply_text('Here are all the questions you have! Type the number of the question that you want to delete')
    
def edit(update, context):
    update.message.reply_text('Choose the deck you’d like to edit! You can choose to delete or add new questions to your deck!')
    edit_buttons(update, context)

def edit_buttons(update, context):
    deck_to_edit = update.message.text
    keyboard = [[InlineKeyboardButton("Add card", callback_data='add card'),
                InlineKeyboardButton("Delete card", callback_data='delete card')],
                [InlineKeyboardButton("Edit card", callback_data='edit card'), 
                InlineKeyboardButton("Remove deck", callback_data='remove deck')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Found ya! Here is your ' + deck_to_edit + '! What do you want to do with the deck?', reply_markup=reply_markup)

def test(update, context):
    update.message.reply_text('Choose the flashcard deck you’d like to be tested on!')

def button(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="You chose to {}!".format(query.data))

def error(update, context):
    """Log Errors caused by Updates."""

    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    #1257761341:AAEL0eO8n4kgvSy3CfJgAAg4EkaME4JQ5sM
    updater = Updater('1257761341:AAEL0eO8n4kgvSy3CfJgAAg4EkaME4JQ5sM', use_context = True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('new', new))
    dp.add_handler(CommandHandler('add', add))
    dp.add_handler(CommandHandler('delete', delete))
    dp.add_handler(CommandHandler('edit', edit))
    dp.add_handler(CommandHandler('test', test))
    #dp.add_handler(CommandHandler('trying', trying))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_error_handler(error)
    #updater.start_polling()
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://memoize-me-telegram-bot.herokuapp.com/' + TOKEN)
    updater.idle()

if __name__ == '__main__':
    main()