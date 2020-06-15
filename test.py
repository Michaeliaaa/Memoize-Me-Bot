
import logging
from telegram.ext import Updater, InlineQueryHandler, CommandHandler,  CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests
import re
import psycopg2
from psycopg2 import Error
import random

import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, CREATE_DECK, VIEW_DECK, DELETE_DECK, ADD_QUESTION, ADD_ANSWER, TESTING, TEST_ANS, DONE = range(9)

reply_keyboard = [['New', 'View'],
                  ['Delete', 'Add'],
                  ['Test', 'Done']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

answer = 0

def start(update, context):
    update.message.reply_text(
        "What do you wanna do?",
        reply_markup=markup)
    return CHOOSING

def new(update, context):
      update.message.reply_text(
        'Create a new deck? What will you name it?')
      return CREATE_DECK

def view(update, context):
      update.message.reply_text(
        'View all your decks? Ok.')
      see(update, context)

def delete(update, context):
      update.message.reply_text(
        'Delete a deck? Which deck?')
      return DELETE_DECK

def add(update, context):
      update.message.reply_text(
        'Add a flashcard? Please type in your question.')
      return ADD_QUESTION

def testing(update, context):
    update.message.reply_text(
        'Time for test. Good luck!')
    #return TESTING
    kaoshi(update, context)

def create(update, context):
      deck(update, context)
      update.message.reply_text("{} succesfully created.".format(getText(update)),
                              reply_markup=markup)
      return CHOOSING

def deck(update, context):
    try:
        connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                  password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                  host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "dbpduk6f0fbp8q")

        cursor = connection.cursor()
        
        postgres_count_query = """select count(*) from decks"""
        cursor.execute(postgres_count_query)
        ID = cursor.fetchone()
        if ID is None:
            ID = 0

        postgres_insert_query = """ INSERT INTO decks (deck_id, deck_name, user_id, card_id) VALUES (%s, %s, %s, %s)"""
        deck_to_insert = (ID, getText(update), getID(update), 0,)
        cursor.execute(postgres_insert_query, deck_to_insert)

        connection.commit()
        count = cursor.rowcount
        print (count, "Record inserted successfully into users table")


    except (Exception, psycopg2.Error) as error :
        if(connection):
            print("Failed to insert record into users table", error)

    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def see(update, context):
      eye(update, context)
      return CHOOSING

def eye(update, context):
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


        #update.message.reply_text("Total number of decks is:", cursor.rowcount)
        update.message.reply_text("Decks created: ")

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

def dele(update, context):
      delrec(update, context)
      update.message.reply_text("{} succesfully deleted.".format(getText(update)),
                              reply_markup=markup)
      return CHOOSING

def delrec(update, context):
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
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def addqna(update, context):
      addq(update, context)
      update.message.reply_text(
        'Now type in your answer.')
      return ADD_ANSWER

def addqna2(update, context):
      adda(update, context)
      update.message.reply_text("Flashcard succesfully added.",
                              reply_markup=markup)
      return CHOOSING

def addq(update, context):
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

def adda(update, context):
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

def kaoshi(update, context):
    kao(update, context)
    #return CHOOSING

def kao(update, context):
    try:
        global answer
        connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                  password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                  host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "dbpduk6f0fbp8q")

        cursor = connection.cursor()

       # postgres_count_query = """select count(*) from questions"""
       # cursor.execute(postgres_count_query)
       # count = cursor.fetchone()
       # if count is None:
       #     id = 0
       # else :
       #     id = random.randint(0, count)

        postgres_question_query = """SELECT qns_info FROM questions"""# WHERE qns_id = 0"""
       # qid = (0,)

        cursor.execute(postgres_question_query)
        question = cursor.fetchall()

        postgres_answer_query = """SELECT ans_info FROM answers"""# WHERE ans_id = 0"""
       # aid = (0,)

        cursor.execute(postgres_answer_query)
        ans = cursor.fetchall()

        update.message.reply_text(question[0][0])
        answer = ans[0][0]
        #testtest(update, context)

        #update.message.reply_text("Total number of decks is:", cursor.rowcount)
        #update.message.reply_text("Decks created: ")

        #for d in results:
        #    update.message.reply_text(d[0])


    except (Exception, psycopg2.Error) as error :
        if(connection):
            print("Failed to view record in q/a table", error)

    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        testtest(update, context)

def testtest(update, context):
    update.message.reply_text("What's the answer?")
    return TEST_ANS

def testq(update, context):
    update.message.reply_text()
    print("here")
    testans(update, context)
    return CHOOSING

def testans(update, context):
    update.message.reply_text("hi!")
    print(answer)
    if (getText(update) != answer):
        update.message.reply_text("Wrong! Again.")
        return TEST_ANS
    update.message.reply_text("Correct!")
    #return CHOOSING

def getID(update):
    return(update.message.chat.id)

def getText(update):
    return(update.message.text)

def done(update, context):
    update.message.reply_text("That's all for today!")
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater("1104454387:AAHpZk9Xp4UaxjvfON0sS6ti_JRBTLOrjuQ", use_context=True)

    dp = updater.dispatcher

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
                                    testing),
                        MessageHandler(Filters.regex('^Done$'),
                                    done)
                       ],

            CREATE_DECK: [MessageHandler(Filters.text,
                                          create)
                        ],
            
            VIEW_DECK: [MessageHandler(Filters.text,
                                        see)
                        ],

            DELETE_DECK: [MessageHandler(Filters.text,
                                          dele)
                        ],
            ADD_QUESTION: [MessageHandler(Filters.text,
                                          addqna)
                        ],
            ADD_ANSWER: [MessageHandler(Filters.text,
                                          addqna2)
                        ],
            TESTING: [MessageHandler(Filters.text,
                                          kaoshi)
                        ],
            TEST_ANS: [MessageHandler(Filters.text,
                                          testq)
                        ]

        },

        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()