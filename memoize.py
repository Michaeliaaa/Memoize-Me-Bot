from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from telegram.ext.dispatcher import run_async
import requests
import re


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
    
def test(update, context):
    update.message.reply_text('Choose the flashcard deck you’d like to be tested on!')

def main():
    updater = Updater('1257761341:AAEL0eO8n4kgvSy3CfJgAAg4EkaME4JQ5sM', use_context = True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('new', new))
    dp.add_handler(CommandHandler('add', add))
    dp.add_handler(CommandHandler('delete', delete))
    dp.add_handler(CommandHandler('edit', edit))
    dp.add_handler(CommandHandler('test', test))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()