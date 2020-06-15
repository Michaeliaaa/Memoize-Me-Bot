import logging
from telegram.ext import Updater, InlineQueryHandler, CommandHandler,  CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests
import re
import psycopg2
from psycopg2 import Error
from random import randint

import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

TOKEN = "1104454387:AAHpZk9Xp4UaxjvfON0sS6ti_JRBTLOrjuQ"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

qns_count = 0
rand_id = 0

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, CREATE_DECK, DELETE_DECK, INSERT_CARD, ADD_QNS, ADD_ANS, TESTING, DONE = range(8)

reply_keyboard = [['New', 'View'],
                  ['Add', 'Delete'],
                  ['Test', 'Done']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

""" Main Commands """ 
# Tell user to click new to create new deck and /help to see all commands
def start(update, context):
    startMessage = "Click new to get started!\n"
    startMessage += "Type /help to see all available commands and what they do.\n"
    update.message.reply_text(startMessage, reply_markup=markup)
    try:
        connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                  password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                  host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "dbpduk6f0fbp8q")

        cursor = connection.cursor()
        postgres_insert_query = """ INSERT INTO users (user_id) VALUES (%s) """
        user_to_insert = (getID(update),)
        cursor.execute(postgres_insert_query, user_to_insert)
        connection.commit()
        count = cursor.rowcount
        print (count, "user inserted successfully into users table")
    except (Exception, psycopg2.Error) as error :
        if (connection):
            print("Failed to insert user into users table: ", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
    return CHOOSING

# Command to create a new deck 
def new(update, context):
    update.message.reply_text(
        '\nLet\'s create a new deck of flashcards!\n'
        'Type /cancel to stop this action.\n\n'
        # Ask user for the name of the new deck
        'Please give your new deck a name.')
    return CREATE_DECK

# Store the deck into the database.
def create_deck(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
    else:
        try:
            connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                    password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                    host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                    port = "5432",
                                    database = "dbpduk6f0fbp8q")
            cursor = connection.cursor()
            # Create unique deck_id by linear probing and store it along with deck_name
            postgres_count_query = """select count(*) from decks"""
            cursor.execute(postgres_count_query)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                DECK_ID = 0
            postgres_insert_query = """ INSERT INTO decks (deck_id, deck_name, user_id, card_id) VALUES (%s, %s, %s, %s)"""
            deck_to_insert = (DECK_ID, getText(update), getID(update), 0,)
            cursor.execute(postgres_insert_query, deck_to_insert)
            connection.commit()
            count = cursor.rowcount
            print (count, "Record inserted successfully into users table")
            update.message.reply_text("{} is created successfully!".format(getText(update)))
            update.message.reply_text("\n Click add to start adding your flashcards!")
        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to insert record into users table", error)
        finally:
            #closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
            return CHOOSING

# Command to view user's decks
def view(update, context):
    update.message.reply_text(
        'Here are all the decks you\'ve created:')
    try:
        connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                  password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                  host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "dbpduk6f0fbp8q")
        cursor = connection.cursor()
        postgres_view_query = """SELECT deck_name FROM decks WHERE user_id = %s"""
        record_to_view = (getID(update),)
        cursor.execute(postgres_view_query, record_to_view)
        results = cursor.fetchall()
        for d in results:
            update.message.reply_text(d[0])
    except (Exception, psycopg2.Error) as error :
        if(connection):
            print("Failed to view record in users table", error)
    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        return CHOOSING

# Command to create a new card 
def add(update, context):
    update.message.reply_text(
        '\nLet\'s create a new flashcard!\n'
        'Type /cancel to stop this action.\n\n'
    )
    #view(update, context)
    update.message.reply_text("Which deck would you like to add a flashcard to?")
    return INSERT_CARD

# Store the card into the database.
def insert_card(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
    else:
        try:
            connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                  password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                  host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "dbpduk6f0fbp8q")
            cursor = connection.cursor()
            # Create unique card_id by linear probing 
            postgres_card_count_query = """SELECT COUNT(*) FROM cards"""
            cursor.execute(postgres_card_count_query)
            CARD_ID = cursor.fetchone()
            if CARD_ID is None:
                CARD_ID = 0
            # Retrieve deck_id from deck_name
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                update.message.reply_text("This deck doesn't exist! You have to create it first! For now, please type an existing deck, or type /cancel.")
                return INSERT_CARD
            # Insert card
            postgres_insert_query = """INSERT INTO cards (card_id, deck_id, qns_id, ans_id) VALUES (%s, %s, %s, %s)"""
            card_to_insert = (CARD_ID, DECK_ID, CARD_ID, CARD_ID,)
            cursor.execute(postgres_insert_query, card_to_insert)
            connection.commit()
            count = cursor.rowcount
            print (count, "card inserted successfully into cards table")
            update.message.reply_text("Please type in your question.")
            return ADD_QNS
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to insert card into cards table: ", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")

def add_qns(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        # delete card that is alr created if user cancel at this phase
    else:
        try:
            connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                    password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                    host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                    port = "5432",
                                    database = "dbpduk6f0fbp8q")

            cursor = connection.cursor()
            postgres_count_query = """select count(*) from questions"""
            cursor.execute(postgres_count_query)
            ID = cursor.fetchone()
            if ID is None:
                ID = 0
            global qns_count
            qns_count = ID
            postgres_insert_query = """ INSERT INTO questions (qns_id, card_id, qns_info) VALUES (%s, %s, %s)"""
            question_to_insert = (ID, ID, getText(update),)
            cursor.execute(postgres_insert_query, question_to_insert)
            connection.commit()
            count = cursor.rowcount
            print (count, "Record inserted successfully into questions table")
        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to insert record into questions table", error)
        finally:
            #closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
            update.message.reply_text('Now type in your answer.')
            return ADD_ANS

def add_ans(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        # delete card and qns that is alr created if user cancel at this phase
    else:
        try:
            connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                    password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                    host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                    port = "5432",
                                    database = "dbpduk6f0fbp8q")
            cursor = connection.cursor()
            postgres_count_query = """select count(*) from answers"""
            cursor.execute(postgres_count_query)
            ID = cursor.fetchone()
            if ID is None:
                ID = 0
            postgres_insert_query = """ INSERT INTO answers (ans_id, card_id, ans_info) VALUES (%s, %s, %s)"""
            answer_to_insert = (ID, ID, getText(update),)
            cursor.execute(postgres_insert_query, answer_to_insert)
            connection.commit()
            count = cursor.rowcount
            print (count, "Record inserted successfully into answers table")
        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to insert record into answers table", error)
        finally:
            #closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
            update.message.reply_text("Flashcard succesfully added.",
                                reply_markup=markup)
            return CHOOSING

#Command to either delete user's decks or questions (?)
def delete(update, context):
    update.message.reply_text(
        'Delete a deck? Which deck?')
    return DELETE_DECK

def delete_deck(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
    else:
        try:
            connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                    password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                    host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                    port = "5432",
                                    database = "dbpduk6f0fbp8q")

            cursor = connection.cursor()
            
            postgres_delete_query = """ DELETE FROM decks WHERE deck_name = %s"""
            record_to_delete = (getText(update),)
            cursor.execute(postgres_delete_query, record_to_delete)
            connection.commit()
            count = cursor.rowcount
            print (count, "Record deleted successfully from decks table")
        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to delete record from decks table", error)
        finally:
            #closing database connection.
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
            update.message.reply_text("{} succesfully deleted.".format(getText(update)),
                                reply_markup=markup)
            return CHOOSING

def test(update, context):
    update.message.reply_text(
        'Time for test. Good luck!')
    find_random(update, context)
    ask_qns(update, context)
    return TESTING
    #endless_ask(update, context)

def find_random(update, context):
    global rand_id
    global qns_count
    rand_id = randint(0, qns_count)
    print(rand_id)
    print(qns_count)

def ask_qns(update, context):
    try:
        connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                    password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                    host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                    port = "5432",
                                    database = "dbpduk6f0fbp8q")
        cursor = connection.cursor()

        postgreSQL_select_query = "SELECT qns_info FROM questions WHERE qns_id = %s"
        global rand_id
        record_to_select = (rand_id,)
        cursor.execute(postgreSQL_select_query, record_to_select)
        qns = cursor.fetchone()
        update.message.reply_text("Question:\n\n{}".format(qns[0]))
        update.message.reply_text("What's the answer?")
    except (Exception, psycopg2.Error) as error :
        print ("Error while fetching data from PostgreSQL", error)
    finally:
        if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")

def testing(update, context):
    if getText(update) == "Done":
        return ConversationHandler.END
    else: 
        try:
            connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                    password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                    host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                    port = "5432",
                                    database = "dbpduk6f0fbp8q")
            cursor = connection.cursor()

            postgreSQL_select_query = "SELECT ans_info FROM answers WHERE ans_id = %s"
            global rand_id
            record_to_select = (rand_id,)
            cursor.execute(postgreSQL_select_query, record_to_select)
            correct_answer = cursor.fetchone()
            user_answer = (getText(update),)
            if user_answer == correct_answer:
                update.message.reply_text("Correct!")
                test(update, context)
            elif user_answer == "Done":
                return ConversationHandler.END
            else:
                update.message.reply_text("Wrong! Try again.")
                return TESTING
        except (Exception, psycopg2.Error) as error :
            print ("Error while fetching data from PostgreSQL", error)
        finally:
            if (connection):
                    cursor.close()
                    connection.close()
                    print("PostgreSQL connection is closed")
            #return CHOOSING

""" Other functions """
# Cancel current actions
def cancel(update, context):
    update.message.reply_text("Action is cancelled successfully.")
    return CHOOSING

# Provides user details of all commands
def help(update, context):
    helpMessage = "Available commands to choose from:\n"
    helpMessage += "new - create new deck\n"
    helpMessage += "view - view all created decks\n"
    helpMessage += "delete - delete decks\n"
    helpMessage += "add - add flashcards to deck\n"
    helpMessage += "test - quiz yourself with selected deck\n"
    helpMessage += "/stats - quiz statistics (for now done)\n"
    update.message.reply_text(helpMessage)
    return CHOOSING

# Retrieve user_id
def getID(update):
    return(update.message.chat.id)

# Retrieve user's response
def getText(update):
    return(update.message.text)

#change this to cancel?
def done(update, context):
    update.message.reply_text("That's all for today! Type /start to start again!")
    return ConversationHandler.END

# Log Errors caused by Updates.
def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater("1104454387:AAHpZk9Xp4UaxjvfON0sS6ti_JRBTLOrjuQ", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("cancel", cancel))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [MessageHandler(Filters.regex('^New$'),
                                    new),
                        MessageHandler(Filters.regex('^Add$'),
                                    add),
                        MessageHandler(Filters.regex('^View$'),
                                    view),
                        MessageHandler(Filters.regex('^Delete$'),
                                    delete),
                        MessageHandler(Filters.regex('^Test$'),
                                    test),
                        MessageHandler(Filters.regex('^Done$'),
                                    done)
                       ],

            CREATE_DECK: [MessageHandler(Filters.text,
                                          create_deck)
                        ],

            DELETE_DECK: [MessageHandler(Filters.text,
                                          delete_deck)
                        ],
            INSERT_CARD: [MessageHandler(Filters.text,
                                          insert_card)
                        ],
            ADD_QNS: [MessageHandler(Filters.text,
                                          add_qns)
                        ],
            ADD_ANS: [MessageHandler(Filters.text,
                                          add_ans)
                        ],
            TESTING: [MessageHandler(Filters.text,
                                          testing)
                        ]

        },
        fallbacks = [CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()