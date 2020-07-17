import logging
from telegram.ext import (Updater, InlineQueryHandler, CommandHandler,  CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext)
from telegram.ext.dispatcher import run_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import requests
import re
import psycopg2
from psycopg2 import Error
from quotes import get_random_quote
import random
import logging
import os
import math
import time
import datetime
import pytz

PORT = int(os.environ.get('PORT', 5000))
TOKEN = "1257761341:AAEL0eO8n4kgvSy3CfJgAAg4EkaME4JQ5sM"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

random_no = 34987203

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, CREATE_DECK, CHOOSE_DELETE, DELETE_DECK, SHOW_QNS, DELETE_QNS, INSERT_CARD, VIEW_QNA, ADD_QNS_TEXT, ADD_QNS_PHOTO, CHOOSE_TYPE, ADD_ANS, ADD_MORE_QNS, DECK_TEST, DECK_TEST_TEST, PRACTICING, TESTING, SHARE_OR_RECEIVE, SHARE_DECK, RECEIVE_DECK, DECK_STATS, DECK_TO_RENAME, RENAME_DECK, SET_OR_UNSET, START_POMODORO, START_AGAIN_POMODORO, REST_POMODORO, START_OR_QUIT, CHOOSE_TIME, DONE = range(30)

reply_keyboard = [['NEW 🆕', 'VIEW 👀'],
                  ['ADD ➕', 'DELETE ⛔'],
                  ['PRACTICE 💪', 'TEST ✍'],
                  ['STATS 📊', 'NEXT ➡️']]
reply_keyboard_2 = [['SHARE 📩', 'RENAME ✏️'],
                    ['SET TIMER ⏱️', 'MOTIVATIONAL QUOTES 😉'],
                    ['DAILY REMINDER 🔔', 'POMODORO TIMER 🍅'],
                    ['BACK ⬅️', 'RESTART BOT 🆘']]
markup = ReplyKeyboardMarkup(reply_keyboard)
markup_2 = ReplyKeyboardMarkup(reply_keyboard_2)

# Connect to db
def connect_db():
        connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                            password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                            host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                            port = "5432",
                            database = "dbpduk6f0fbp8q")
        return connection

""" Main Commands """ 
# Tell user to click new to create new deck and /help to see all commands
def start(update, context):
    startMessage = "Click NEW to get started!\n\n"
    startMessage += "Need help? 🆘\nClick /help to see all available commands and what they do.\n"
    update.message.reply_text(startMessage, reply_markup=markup)
    try:
        connection = connect_db()
        cursor = connection.cursor()
        postgres_insert_query = """INSERT INTO users (user_id) VALUES (%s) """
        user_to_insert = (getID(update),)
        cursor.execute(postgres_insert_query, user_to_insert)
        connection.commit()
        count = cursor.rowcount
        print (count, "user inserted successfully into users table")
    except (Exception, psycopg2.Error):# as error :
        if (connection):
            # print("Failed to insert user into users table: ", error)
            print("User already registered")
    finally:
        if (connection):
            cursor.close()
            connection.close()
            # print("PostgreSQL connection is closed")
    return CHOOSING

# Store the deck into the database.
def new(update, context):
    update.message.reply_text(
        '\nLet\'s create a new deck of flashcards!\n\n'
        'Type /cancel to stop this action and choose another option.\n\n')
    update.message.reply_text('Please give your new deck a name.')
    return CREATE_DECK

def create_deck(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            # Check if deck_name already existed
            postgres_search_query = """SELECT COUNT(*) FROM decks WHERE deck_name = %s AND user_id = %s"""
            deck_to_insert = (getText(update), getID(update),)
            cursor.execute(postgres_search_query, deck_to_insert)
            CHECK = cursor.fetchone()
            if CHECK[0] == 0:
                # Insert deck
                postgres_insert_query = """INSERT INTO decks (deck_id, deck_name, user_id) VALUES (DEFAULT, %s, %s)"""
                cursor.execute(postgres_insert_query, deck_to_insert)
                connection.commit()
                count = cursor.rowcount
                print (count, "deck inserted successfully into decks table")
                update.message.reply_text("{} is created successfully!".format(getText(update)))
                update.message.reply_text("\n Click ADD to start adding your flashcards!")
                return CHOOSING
            else:
                update.message.reply_text("You already have a deck called {}. Please try another name. \n\n Type /cancel to stop this action and choose another option.".format(getText(update)))
                return CREATE_DECK
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to insert deck into decks table", error)
        finally:
            # closing database connection.
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")

# View user's decks
def view_deck(update, context):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        postgres_view_query = """SELECT deck_name FROM decks WHERE user_id = %s"""
        deck_to_view = (getID(update),)
        cursor.execute(postgres_view_query, deck_to_view)
        results = cursor.fetchall()
        lst_of_decks = list(d[0] for d in results)
        if len(lst_of_decks) == 0:
            update.message.reply_text("You don't have any decks right now.\nClick NEW to create your first deck!", reply_markup=markup)
            return CHOOSING
        else:
            str = "Here are all the decks you\'ve created:\n"
            for i in lst_of_decks:
                str = str + i + "\n"
            update.message.reply_text(str)
            update.message.reply_text(
            '\nWhich deck would you like to look into?\n\n'
            'Type /cancel to stop this action and choose another option.\n\n')
            return VIEW_QNA
    except (Exception, psycopg2.Error) as error :
        if(connection):
            print("Failed to view deck in decks table", error)
    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            # print("PostgreSQL connection is closed")

def view_qna(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            is_check = True
            connection = connect_db()
            cursor = connection.cursor()
            # Retrieve deck_id from deck_name
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                update.message.reply_text("This deck doesn't exist, you have to create it first! \n\nFor now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                is_check = False
                return VIEW_QNA
            deck_id_to_insert = (DECK_ID)
            # Retrieve qns_info from deck_id
            postgres_view_qns_query = """SELECT qns_info, is_text FROM questions INNER JOIN cards ON questions.card_id = cards.card_id WHERE cards.deck_id = %s"""
            cursor.execute(postgres_view_qns_query, deck_id_to_insert)
            questions = cursor.fetchall()
            lst_of_qns = list(q[0] for q in questions)
            lst_text = list(q[1] for q in questions)
            if len(lst_of_qns) == 0:
                update.message.reply_text("There aren't any flashcards in this deck.\n\nAdd flashcards by clicking ADD!")
                return CHOOSING
            a = lst_of_qns
                # update.message.reply_text('Here are all your questions:')
                # for qns in lst_of_qns:
                #      update.message.reply_text(qns)
            # Retrieve ans_info from deck_id
            postgres_view_ans_query = """SELECT ans_info FROM answers INNER JOIN cards ON answers.card_id = cards.card_id WHERE cards.deck_id = %s"""
            cursor.execute(postgres_view_ans_query, deck_id_to_insert)
            answers = cursor.fetchall()
            lst_of_ans = list(a[0] for a in answers)
            b = lst_of_ans
                # update.message.reply_text('Here are all your answers:')
                # for ans in lst_of_ans:
                #     update.message.reply_text(ans)
            # Interweave lst_of_qns and lst_of_ans to create a new list with order of qns then ans
            c = a + b
            c[::2] = a
            c[1::2] = b
            print(c)
            index = 1
            for idx, i in enumerate(c):
                if idx % 2 == 0:
                    print(lst_text)
                    #is_text = lst_text[(int(i) - 1)]
                    #print(i)
                    print(lst_text[index-1])
                    if(lst_text[index - 1]):
                        update.message.reply_text(("Question {}: \n\n" + i).format(str(index)))
                        index = index + 1
                    else:
                        update.message.reply_text(("Question {}: \n\n").format(str(index)))
                        chat_id = update.message.chat_id
                        context.bot.send_photo(chat_id=chat_id, photo = i)
                        index = index + 1
                else:
                    if idx != len(c) - 1:
                        update.message.reply_text("Answer: \n\n" + i)
                        # update.message.reply_text("🔽")
                    else:
                        update.message.reply_text("Answer: " + i)
            update.message.reply_text("That's all you have in this deck!")
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to view qna from the tables", error)
            return CHOOSING
        finally:
            # closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")
            if (is_check):    
                return CHOOSING

def deck_list(update, context):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        postgreSQL_select_query = "SELECT deck_name FROM decks WHERE user_id = %s"
        userid_to_insert = (getID(update),)
        cursor.execute(postgreSQL_select_query, userid_to_insert)
        decks = cursor.fetchall()
        def get_deck_list(decks):
            str = ""
            # str = "Your decks:\n"
            list_of_deck = []
            for deck_name in decks:
                list_of_deck.append(deck_name[0])
            for i in list_of_deck:
                str = str + i + "\n"
            return str
        if len(get_deck_list(decks)) == 0:
            update.message.reply_text("You don't have any decks right now.\nClick NEW to create your first deck!", reply_markup=markup)
            return 0
        else: 
            update.message.reply_text("Your decks: \n" + get_deck_list(decks))
    except (Exception, psycopg2.Error) as error :
        print ("Error while fetching data from PostgreSQL", error)
    finally:
        if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")

# Store the card into the database.
def add(update, context):
    if deck_list(update, context) == 0:
        return CHOOSING
    else:
        update.message.reply_text(
        '\nLet\'s create a new flashcard!\n\n'
        'Type /cancel to stop this action and choose another option.\n\n')
        update.message.reply_text("Which deck would you like to add a flashcard to?")
        return INSERT_CARD

def insert_card(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
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
                update.message.reply_text("This deck doesn't exist, you have to create it first! \n\nFor now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                return INSERT_CARD
            # Insert card
            postgres_insert_query = """INSERT INTO cards (card_id, deck_id, qns_id, ans_id, num_attempts, num_correct) VALUES (DEFAULT, %s, DEFAULT, DEFAULT, 0, 0)"""
            card_to_insert = (DECK_ID,)
            cursor.execute(postgres_insert_query, card_to_insert)
            connection.commit()
            count = cursor.rowcount
            
            postgres_score_query = """INSERT INTO scores (user_id, deck_id, qns_count) VALUES (%s, %s, DEFAULT)"""
            score_to_insert = (getID(update), DECK_ID,)
            cursor.execute(postgres_score_query, score_to_insert)
            connection.commit()

            print (count, "card inserted successfully into cards table")
            update.message.reply_text("Adding flashcard to {} deck.".format(getText(update)))
            # update.message.reply_text("Please type in your question, or send a picture.")
            # return ADD_QNS
            reply_keyboard = [['Text', 'Photo']]
            update.message.reply_text("Are you adding a text or photo?",
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return CHOOSE_TYPE
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to insert card into cards table: ", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")

def choose_type(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    elif getText(update) == "Text":
        update.message.reply_text("Please type in your question.")
        return ADD_QNS_TEXT
    elif getText(update) == "Photo":
        update.message.reply_text("Please send in your photo.")
        return ADD_QNS_PHOTO
    else:
        reply_keyboard = [['Text', 'Photo']]
        update.message.reply_text("Are you adding a text or photo?",
                            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return CHOOSE_TYPE

def get_photo(update, context: CallbackContext):
    file = context.bot.get_file(update.message.photo[-1].file_id)
    url = file['file_id']
    print(url)
    #chat_id = update.message.chat_id
    #context.bot.send_photo(chat_id=chat_id, photo=url)
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            postgres_count_query = """SELECT COUNT(*) FROM questions"""
            cursor.execute(postgres_count_query)
            ID = cursor.fetchone()
            if ID is None:
                ID = 0
            global qns_count
            qns_count = ID
            # Add question
            postgres_insert_query = """INSERT INTO questions (qns_id, card_id, qns_info, is_text) VALUES (DEFAULT, DEFAULT, %s, False)"""
            question_to_insert = (url,)
            cursor.execute(postgres_insert_query, question_to_insert)
            connection.commit()
            count = cursor.rowcount
            print (count, "question inserted successfully into questions table")
        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to insert question into questions table", error)
        finally:
            # closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")
            update.message.reply_text('Now type in your answer.')
            return ADD_ANS

def add_qns(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            postgres_count_query = """SELECT COUNT(*) FROM questions"""
            cursor.execute(postgres_count_query)
            ID = cursor.fetchone()
            if ID is None:
                ID = 0
            global qns_count
            qns_count = ID
            # Add question
            postgres_insert_query = """INSERT INTO questions (qns_id, card_id, qns_info, is_text) VALUES (DEFAULT, DEFAULT, %s, True)"""
            question_to_insert = (getText(update),)
            cursor.execute(postgres_insert_query, question_to_insert)
            connection.commit()
            count = cursor.rowcount
            print (count, "question inserted successfully into questions table")
        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to insert question into questions table", error)
        finally:
            # closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")
            update.message.reply_text('Now type in your answer.')
            return ADD_ANS

def add_ans(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            postgres_count_query = """SELECT COUNT(*) FROM answers"""
            cursor.execute(postgres_count_query)
            ID = cursor.fetchone()
            if ID is None:
                ID = 0
            postgres_insert_query = """INSERT INTO answers (ans_id, card_id, ans_info) VALUES (DEFAULT, DEFAULT, %s)"""
            answer_to_insert = (getText(update),)
            cursor.execute(postgres_insert_query, answer_to_insert)
            connection.commit()
            count = cursor.rowcount
            print (count, "answer inserted successfully into answers table")
        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to insert answer into answers table", error)
        finally:
            # closing database connection.
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")
            update.message.reply_text("Flashcard successfully added.")
            reply_keyboard = [['Yes ✅', 'No ⛔']]
            update.message.reply_text("Would you like add more flashcards to this deck?",
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            # update.message.reply_text("Would you like add more flashcards to this deck?\n\nType YES to continue and type NO to stop and choose another action.")
            return ADD_MORE_QNS
            #return CHOOSING

def add_more_qns(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    elif getText(update).lower() == "yes ✅":
        print("Add more: Yes")
        try: 
            connection = connect_db()
            cursor = connection.cursor()
            # Retrieve deck_id
            postgres_deck_query = """SELECT deck_id FROM scores WHERE user_id = (%s)"""
            user_id = (getID(update), )
            cursor.execute(postgres_deck_query, user_id)
            deck_id = cursor.fetchone()
            print("Deck ID: " + str(deck_id))
            insert_more_cards(update, context, deck_id)
            reply_keyboard = [['Text', 'Photo']]
            update.message.reply_text("Are you adding a text or photo?",
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return CHOOSE_TYPE
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to add more question", error)
        finally:
            # closing database connection.
            if (connection):
                cursor.close()
                connection.close()
    elif getText(update).lower() == "no ⛔":
        print("Add more: No")
        update.message.reply_text("Alright, no more flashcards will be added.", reply_markup=markup)
        try: 
            connection = connect_db()
            cursor = connection.cursor()
            # Delete record 
            postgres_delete_query = """DELETE FROM scores WHERE user_id = %s"""
            record_to_delete = (getID(update),)
            cursor.execute(postgres_delete_query, record_to_delete)
            connection.commit()
            # print("Record deleted successfully")
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print(error)
        finally:
            # closing database connection.
            if (connection):
                cursor.close()
                connection.close()
            return CHOOSING
    else:
        print("invalid output")
        update.message.reply_text("Please only type YES or NO.")
        return ADD_MORE_QNS

def insert_more_cards(update, context, deck_id):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            # Create unique card_id by linear probing 
            postgres_card_count_query = """SELECT COUNT(*) FROM cards"""
            cursor.execute(postgres_card_count_query)
            CARD_ID = cursor.fetchone()
            if CARD_ID is None:
                CARD_ID = 0
            
            # Insert card
            postgres_insert_query = """INSERT INTO cards (card_id, deck_id, qns_id, ans_id, num_attempts, num_correct) VALUES (DEFAULT, %s, DEFAULT, DEFAULT, 0, 0)"""
            card_to_insert = (deck_id,)
            cursor.execute(postgres_insert_query, card_to_insert)
            connection.commit()
            count = cursor.rowcount
            
            postgres_score_query = """INSERT INTO scores (user_id, deck_id, qns_count) VALUES (%s, %s, DEFAULT)"""
            score_to_insert = (getID(update), deck_id,)
            cursor.execute(postgres_score_query, score_to_insert)
            connection.commit()

            print (count, "card inserted successfully into cards table")
            # update.message.reply_text("Please type in your question, or send a picture.")
            return CHOOSE_TYPE
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to insert card into cards table: ", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")

# Command to either delete user's decks or questions
def delete(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else: 
        #update.message.reply_text(
        #    'If you would like to delete an entire deck, type DECK.\n\n'
        #    'If you would like to delete a question from a specific deck, type QNS.\n\n'
        #    'Type /cancel to stop this action and choose another option.')
        #return CHOOSE_DELETE
        reply_keyboard = [['DECK', 'QNS']]
        update.message.reply_text(
            'If you would like to delete an entire deck, choose DECK.\n\n'
            'If you would like to delete a question from a specific deck, choose QNS.\n\n'
            'Type /cancel to stop this action and choose another option.',
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            # update.message.reply_text("Would you like add more flashcards to this deck?\n\nType YES to continue and type NO to stop and choose another action.")
        return CHOOSE_DELETE
        
def choose_delete(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    elif getText(update).lower() == "deck":
        if deck_list(update, context) == 0:
            return CHOOSING
        else: 
            update.message.reply_text('Which deck would you like to delete?')
        return DELETE_DECK
    elif getText(update).lower() == "qns":
        if deck_list(update, context) == 0:
            return CHOOSING
        else: 
            update.message.reply_text('Which deck would you like to choose?')
            return SHOW_QNS
    else:
        #update.message.reply_text("Type either DECK or QNS, or type /cancel to stop this action and choose another option.")
        reply_keyboard = [['DECK', 'QNS']]
        update.message.reply_text(
            'Choose either DECK or QNS, or type /cancel to stop this action and choose another option.',
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return CHOOSE_DELETE
        
def delete_deck(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                update.message.reply_text("This deck doesn't exist, you have to create it first! \n\nFor now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                return DELETE_DECK
            # Find card_id linked to the deck_name
            postgreSQL_select_query = """SELECT card_id FROM cards INNER JOIN decks ON cards.deck_id = decks.deck_id WHERE deck_name = %s AND user_id = %s"""
            deck_to_delete = (getText(update), getID(update),)
            cursor.execute(postgreSQL_select_query, deck_to_delete)
            cardids = cursor.fetchall()
            print("Card IDs: " + str(cardids))
            for cardid in cardids:
                # Delete card
                postgres_delete_card_query = """DELETE FROM cards WHERE card_id = %s"""
                cursor.execute(postgres_delete_card_query, cardid)
                connection.commit()
                print ("card {} deleted successfully from cards table".format(cardid))
                # Delete question
                postgres_delete_qns_query = """DELETE FROM questions WHERE card_id = %s"""
                cursor.execute(postgres_delete_qns_query, cardid)
                connection.commit()
                print ("question {} deleted successfully from questions table".format(cardid))
                # Delete answer
                postgres_delete_ans_query = """DELETE FROM answers WHERE card_id = %s"""
                cursor.execute(postgres_delete_ans_query, cardid)
                connection.commit()
                print ("answer {} deleted successfully from answers table".format(cardid))
            # Delete deck
            postgres_delete_deck_query = """DELETE FROM decks WHERE deck_name = %s AND user_id = %s"""
            cursor.execute(postgres_delete_deck_query, deck_to_delete)
            connection.commit()
            count = cursor.rowcount
            print (count, "deck deleted successfully from decks table")
            update.message.reply_text("{} successfully deleted.".format(getText(update)),
                                reply_markup=markup)
            return CHOOSING 
        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to delete deck from decks table", error)
        finally:
            postgres_index_check_query = """SELECT to_regclass('index');"""
            cursor.execute(postgres_index_check_query)
            check = cursor.fetchone()
            # closing database connection.
            print("Index table existence: " + str(check[0] == "index"))
            if ((check[0] == 'index') == True):
                postgresSQL_delete_query = """DROP TABLE IF EXISTS index"""
                cursor.execute(postgresSQL_delete_query)
                connection.commit()
            print("Table index deleted successfully in PostgreSQL ")
            if(connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")  

def show_qns(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                update.message.reply_text("This deck doesn't exist, you have to create it first! \n\nFor now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                return SHOW_QNS
            # Retrieve number of cards in the deck
            postgres_count_qns_query = """SELECT COUNT(*) FROM cards INNER JOIN decks ON cards.deck_id = decks.deck_id WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_count_qns_query, deck_name_and_id)
            count = cursor.fetchone()
            print("Number of qns in the deck: " + str(count[0]))
            # Create index table for numbering
            create_index_table_query = '''CREATE TABLE IF NOT EXISTS index
                    (qns_index INT PRIMARY KEY,
                    qns_id INT NOT NULL); '''
            cursor.execute(create_index_table_query)
            connection.commit()
            print("Table index created successfully in PostgreSQL")
            deck_id_to_insert = (DECK_ID)
            # Retrieve qns_id from deck_id
            postgres_qns_id_query = """SELECT qns_id FROM cards WHERE cards.deck_id = %s"""
            cursor.execute(postgres_qns_id_query, deck_id_to_insert)
            ids = cursor.fetchall()
            print("Qns IDs: " + str(ids))
            # Retrieve qns_info from deck_id
            postgres_view_qns_query = """SELECT qns_info, is_text FROM questions INNER JOIN cards ON questions.card_id = cards.card_id WHERE cards.deck_id = %s"""
            cursor.execute(postgres_view_qns_query, deck_id_to_insert)
            questions = cursor.fetchall()
            lst_of_qns = list(q[0] for q in questions)
            lst_text = list(q[1] for q in questions)
            if len(lst_of_qns) == 0:
                update.message.reply_text("There aren't any flashcards in this deck.\n\nAdd flashcards by clicking ADD!", reply_markup=markup)
                return CHOOSING
            else:
                # Insert qns_index and qns_id into the index table
                index = 1
                for id in ids:
                    print("Qns ID: " + str(id))
                    postgres_insert_query = """INSERT INTO index (qns_index, qns_id) VALUES (%s, %s)"""
                    record_to_insert = (index, id[0],)
                    cursor.execute(postgres_insert_query, record_to_insert)
                    connection.commit()
                    print("index {} created successfully".format(index))
                    index = index + 1
                    print("All indexes are inserted successfully")
                # Show questions
                update.message.reply_text('Here are all your questions:')
                qns_no = 1
                for qns in lst_of_qns:
                     print(lst_text[qns_no - 1])
                     if (lst_text[qns_no - 1]):
                        update.message.reply_text("Question {}: ".format(str(qns_no)) + qns)
                        qns_no = qns_no + 1
                     else:
                        update.message.reply_text("Question {}: ".format(str(qns_no)))                      
                        chat_id = update.message.chat_id
                        context.bot.send_photo(chat_id=chat_id, photo = qns)
                        qns_no = qns_no + 1
                update.message.reply_text('Please type the question number of the question that you would like to delete. For multiple deletion, please use comma to separate the question. \n\n'
                                            'Type /cancel to stop this action and choose another option.')
                return DELETE_QNS
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to view qna from the tables", error)
            return CHOOSING
        finally:
            postgres_index_check_query = """SELECT to_regclass('index');"""
            cursor.execute(postgres_index_check_query)
            check = cursor.fetchone()
            print("Index table existence: " + str(check[0] == "index"))
            # closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed") 
    
def delete_qns(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            text = getText(update)
            result = [x.strip() for x in text.split(',')]
            list_of_card_id = []
            for i in result:
                print("Question(s) to delete: " + str(i))
                # Retrieve qns_id from index
                postgres_select_query = """SELECT qns_id FROM index WHERE qns_index = %s"""
                qns_index_to_insert = (i,)
                cursor.execute(postgres_select_query, qns_index_to_insert)
                Card_ID = cursor.fetchone()
                print("Card ID: " + str(Card_ID))
                list_of_card_id.insert(len(list_of_card_id), Card_ID)
            print("List of card ids to delete: " + str(list_of_card_id))
            for card_id in list_of_card_id:
                # Delete card
                postgres_delete_card_query = """DELETE FROM cards WHERE card_id = %s"""
                cursor.execute(postgres_delete_card_query, card_id)
                connection.commit()
                print ("card {} deleted successfully from cards table".format(card_id))
                # Delete question
                postgres_delete_qns_query = """DELETE FROM questions WHERE card_id = %s"""
                cursor.execute(postgres_delete_qns_query, card_id)
                connection.commit()
                print ("question {} deleted successfully from questions table".format(card_id))
                # Delete answer
                postgres_delete_ans_query = """DELETE FROM answers WHERE card_id = %s"""
                cursor.execute(postgres_delete_ans_query, card_id)
                connection.commit()
                print ("answer {} deleted successfully from answers table".format(card_id))
            update.message.reply_text('{} flashcard(s) has been deleted successfully.'.format(len(list_of_card_id)), reply_markup=markup)
            # Delete index table
            postgresSQL_delete_query = """DROP TABLE IF EXISTS index"""
            cursor.execute(postgresSQL_delete_query)
            connection.commit()
            print("Table index deleted successfully in PostgreSQL ")
            return CHOOSING
        except (Exception, psycopg2.Error) as error :
            postgresSQL_delete_query = """DROP TABLE IF EXISTS index"""
            cursor.execute(postgresSQL_delete_query)
            connection.commit()
            print("Table index deleted successfully in PostgreSQL ")
            if (connection):
                print("Failed to view qna from the tables", error)
                return CHOOSING
        finally:
            postgres_index_check_query = """SELECT to_regclass('index');"""
            cursor.execute(postgres_index_check_query)
            check = cursor.fetchone()
            # closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed") 
            print("Index table existence: " + str(check[0] == "index"))
            if ((check[0] == 'index') == False):
                return CHOOSING

# Practice / Test
def practice(update, context):
    if deck_list(update, context) == 0:
        return CHOOSING
    else:
        update.message.reply_text(
            'Practice makes perfect! 👍\n\n'
            'Type /cancel to stop this action or want to stop and choose another option.\n\n')
        update.message.reply_text("Which deck would you like to practice?")
        return DECK_TEST

def deck_test(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            is_check = True
            connection = connect_db()
            cursor = connection.cursor()
            # Retrieve deck_id from deck_name
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                update.message.reply_text("This deck doesn't exist, you have to create it first! \n\nFor now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                is_check = False
                return DECK_TEST
            else:
                postgres_card_query = """SELECT card_id FROM cards WHERE deck_id = (%s)"""
                #check_card_in_deck = (DECK_ID)
                cursor.execute(postgres_card_query, DECK_ID)
                isCard = cursor.fetchone()
                if isCard is None:
                    update.message.reply_text("There aren't any flashcards in this deck! \n\nClick ADD to start adding flashcards! \n\nFor now, please type a deck with flashcards, or type /cancel to stop this action and choose another option.")
                    is_check = False
                    return DECK_TEST
                print("Deck ID: " + str(list(DECK_ID).pop(0)))
                # Create a copy of card_id
                create_copy_table_query = '''CREATE TABLE IF NOT EXISTS copy AS SELECT card_id FROM cards WHERE deck_id = %s'''
                deck_to_select =  (DECK_ID,)
                cursor.execute(create_copy_table_query, deck_to_select)
                connection.commit()
                print("Table copy created successfully in PostgreSQL ")
                ask_qns_practice(update, context, DECK_ID)
                return PRACTICING
        except (Exception, psycopg2.Error) as error :
            print ("Error while fetching data from PostgreSQL", error)
        finally:
            postgres_copy_check_query = """SELECT to_regclass('copy');"""
            cursor.execute(postgres_copy_check_query)
            check = cursor.fetchone()
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")
            print("Copy table existence: " + str(check[0] == "copy"))
            if ((check[0] == 'copy') == False and is_check):
                return CHOOSING 

def ask_qns_practice(update, context, deck_id):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            # Check how many remaining questions left
            postgres_copy_count_query = """SELECT COUNT(*) FROM copy"""
            cursor.execute(postgres_copy_count_query)
            remaining = cursor.fetchone()
            # total_qns = remaining[0]
            update.message.reply_text("Remaining questions: " + str(list(remaining).pop(0)))
            if list(remaining).pop(0) == 0:

                # Count score
                postgres_total_query = """SELECT COUNT(*) FROM scores WHERE user_id = (%s)"""
                user_total = (getID(update),)
                cursor.execute(postgres_total_query, user_total)
                total_qns = cursor.fetchone()

                postgres_score_query = """SELECT COUNT(*) FROM scores WHERE user_id = (%s) AND is_correct = True"""
                user_score = (getID(update),)
                cursor.execute(postgres_score_query, user_score)
                score = cursor.fetchone()

                postgres_skip_query = """SELECT COUNT(*) FROM scores WHERE user_id = (%s) AND is_correct = False"""
                user_skip = (getID(update),)
                cursor.execute(postgres_skip_query, user_skip)
                skip = cursor.fetchone()

                update.message.reply_text("You have finished practicing. Good job! 👏")
                update.message.reply_text("You got {} out of {} questions correct. You skipped {} questions. Try out TEST for a more serious test, without the option to skip!".format(score[0], total_qns[0], skip[0]))
                postgresSQL_delete_query = """DROP TABLE IF EXISTS copy"""
                cursor.execute(postgresSQL_delete_query)
                connection.commit()
                print("Table copy deleted successfully in PostgreSQL ")
                # Delete record
                postgres_delete_query = """DELETE FROM check_ans WHERE user_id = %s"""
                record_to_delete = (getID(update),)
                cursor.execute(postgres_delete_query, record_to_delete)
                connection.commit()

                postgres_del_query = """DELETE FROM scores WHERE user_id = %s"""
                record_to_del = (getID(update),)
                cursor.execute(postgres_del_query, record_to_del)
                connection.commit()

                return CHOOSING
            else:
                # Retrive questions from deck
                postgres_select_card_query = """SELECT card_id FROM copy
                                                ORDER BY RANDOM()
                                                LIMIT 1"""
                deck_to_select =  deck_id
                cursor.execute(postgres_select_card_query, deck_to_select)
                card_id = cursor.fetchone()
                print("card_id: " + str(list(card_id).pop(0)))

                # Keep track of scores
                postgres_score_query = """INSERT INTO scores (user_id, deck_id, qns_count) VALUES (%s, %s, DEFAULT)"""
                score_to_insert = (getID(update), deck_id,)
                cursor.execute(postgres_score_query, score_to_insert)
                connection.commit()

                # Insert card_id that is already tested
                postgres_insert_query = """INSERT INTO check_ans (user_id, card_id, deck_id) VALUES (%s, %s, %s)"""
                record_to_insert = (getID(update), card_id, deck_id,)
                cursor.execute(postgres_insert_query, record_to_insert)
                connection.commit()


                postgres_text_query = "SELECT is_text FROM questions WHERE qns_id = %s"
                text_to_select = card_id
                cursor.execute(postgres_text_query, text_to_select)
                is_text = cursor.fetchone()[0]
                print(is_text)

                if (not is_text):
                    postgreSQL_select_query = "SELECT qns_info FROM questions WHERE qns_id = %s"
                    card_to_select = card_id
                    cursor.execute(postgreSQL_select_query, card_to_select)
                    qns = cursor.fetchone()[0]
                    update.message.reply_text("Question:\n\n")
                    chat_id = update.message.chat_id
                    context.bot.send_photo(chat_id=chat_id, photo = qns)

                    update.message.reply_text("What's the answer? Type /skip if you wish to skip the question.")

                    # Delete card_id that is already tested from copy 
                    postgres_delete_query = """DELETE FROM copy WHERE card_id = %s"""
                    cursor.execute(postgres_delete_query, card_to_select)

                else: 
                    postgreSQL_select_query = "SELECT qns_info FROM questions WHERE qns_id = %s"
                    card_to_select = card_id
                    cursor.execute(postgreSQL_select_query, card_to_select)
                    qns = cursor.fetchone()
                    update.message.reply_text("Question:\n\n{}".format(qns[0]))
                    update.message.reply_text("What's the answer? Type /skip if you wish to skip the question.")

                    # Delete card_id that is already tested from copy 
                    postgres_delete_query = """DELETE FROM copy WHERE card_id = %s"""
                    cursor.execute(postgres_delete_query, card_to_select)
        except (Exception, psycopg2.Error) as error :
            print ("Error while fetching data from PostgreSQL", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()

def practicing(update, context):
    try:
        connection = connect_db()
        cursor = connection.cursor()

        if (getText(update) == "Done"):
            # Delete record
            postgres_delete_query = """ DELETE FROM check_ans WHERE user_id = %s"""
            record_to_delete = (getID(update),)
            cursor.execute(postgres_delete_query, record_to_delete)
            connection.commit()
            done(update, context)
            postgresSQL_delete_query = """DROP TABLE IF EXISTS copy"""
            cursor.execute(postgresSQL_delete_query)
            connection.commit()
            print("Table copy deleted successfully in PostgreSQL ")
            return CHOOSING
        elif (getText(update) == "/cancel"):
            # Delete record
            postgres_delete_query = """ DELETE FROM check_ans WHERE user_id = %s"""
            record_to_delete = (getID(update),)
            cursor.execute(postgres_delete_query, record_to_delete)
            connection.commit()
            cancel(update, context)
            postgresSQL_delete_query = """DROP TABLE IF EXISTS copy"""
            cursor.execute(postgresSQL_delete_query)
            connection.commit()
            print("Table copy deleted successfully in PostgreSQL ")
            return CHOOSING

        # Find the deck_id
        postgres_deck_query = "SELECT deck_id FROM check_ans WHERE user_id = %s"
        record_to_deck = (getID(update),)
        cursor.execute(postgres_deck_query, record_to_deck)
        deck_id = cursor.fetchone()

        # Find correct ans_id
        postgres_find_query = "SELECT card_id FROM check_ans WHERE user_id = %s"
        user_id_to_select = (getID(update),)
        cursor.execute(postgres_find_query, user_id_to_select)
        card_id = cursor.fetchone()

        postgreSQL_select_query = "SELECT ans_info FROM answers WHERE ans_id = %s"
        card_to_select = card_id
        cursor.execute(postgreSQL_select_query, card_to_select)
        correct_answer = cursor.fetchone()
        user_answer = (getText(update),)
        if (user_answer[0].lower() == correct_answer[0].lower()):
            update.message.reply_text("Correct!")

            # Update score
            postgres_score_query = """UPDATE scores SET is_correct = (%s) WHERE user_id = (%s) AND qns_count IN(SELECT max(qns_count) FROM scores)"""
            score_to_insert = (True, getID(update),)
            cursor.execute(postgres_score_query, score_to_insert)
            connection.commit()

            # Delete from check_ans
            postgres_delete_query = """DELETE FROM check_ans WHERE user_id = %s"""
            record_to_delete = (getID(update),)
            cursor.execute(postgres_delete_query, record_to_delete)
            connection.commit()
            # Delete from copy
            postgresSQL_delete_query = """DELETE FROM copy WHERE card_id = %s"""
            cursor.execute(postgresSQL_delete_query, card_to_select)
            connection.commit()
            ask_qns_practice(update, context, deck_id)
        elif (getText(update) == "/skip"):

            # Update score
            postgres_score_query = """UPDATE scores SET is_correct = (%s) WHERE user_id = (%s) AND qns_count IN(SELECT max(qns_count) FROM scores)"""
            score_to_insert = (False, getID(update),)
            cursor.execute(postgres_score_query, score_to_insert)
            connection.commit()

            update.message.reply_text("Question skipped. Try harder next time!")
            update.message.reply_text("The answer is: {}".format(correct_answer[0]))
            # Delete from check_ans
            postgres_delete_query = """DELETE FROM check_ans WHERE user_id = %s"""
            record_to_delete = (getID(update),)
            cursor.execute(postgres_delete_query, record_to_delete)
            connection.commit()
            # Delete from copy
            postgresSQL_delete_query = """DELETE FROM copy WHERE card_id = %s"""
            cursor.execute(postgresSQL_delete_query, card_to_select)
            connection.commit()
            ask_qns_practice(update, context, deck_id)
        else:
            update.message.reply_text("Wrong! Try again.")
            return PRACTICING
    except (Exception, psycopg2.Error) as error :
        print ("Error while fetching data from PostgreSQL", error)
    finally:
        postgres_copy_check_query = """SELECT to_regclass('copy');"""
        cursor.execute(postgres_copy_check_query)
        check = cursor.fetchone()
        if (connection):
            cursor.close()
            connection.close()
            # print("PostgreSQL connection is closed")
        print("Copy table existence: " + str(check[0] == "copy"))
        if ((check[0] == 'copy') == False):
            return CHOOSING 

def test(update, context):
    if deck_list(update, context) == 0:
        return CHOOSING
    else:
        update.message.reply_text(
        'Time for test! Good luck 🍀!\n\n'
        'Type /cancel to stop this action or want to stop and choose another option.\n\n')
        update.message.reply_text("Which deck would you like to be tested on?")
        return DECK_TEST_TEST

def deck_test_test(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            is_check = True
            connection = connect_db()
            cursor = connection.cursor()
            # Retrieve deck_id from deck_name
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                update.message.reply_text("This deck doesn't exist, you have to create it first! \n\nFor now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                is_check = False
                return DECK_TEST_TEST
            else:
                postgres_card_query = """SELECT card_id FROM cards WHERE deck_id = (%s)"""
                # Check_card_in_deck = (DECK_ID)
                cursor.execute(postgres_card_query, DECK_ID)
                isCard = cursor.fetchone()
                if isCard is None:
                    update.message.reply_text("There aren't any flashcards in this deck! \n\nClick ADD to start adding flashcards! \n\nFor now, please type a deck with flashcards, or type /cancel to stop this action and choose another option.")
                    is_check = False
                    return DECK_TEST_TEST
                print("Deck ID: " + str(list(DECK_ID).pop(0)))
                # Create a copy of card_id
                create_copy_table_query = '''CREATE TABLE IF NOT EXISTS copy AS SELECT card_id FROM cards WHERE deck_id = %s'''
                deck_to_select =  (DECK_ID,)
                cursor.execute(create_copy_table_query, deck_to_select)
                connection.commit()
                print("Table copy created successfully in PostgreSQL ")
                ask_qns_test(update, context, DECK_ID)
                return TESTING
        except (Exception, psycopg2.Error) as error :
            print ("Error while fetching data from PostgreSQL", error)
        finally:
            postgres_copy_check_query = """SELECT to_regclass('copy');"""
            cursor.execute(postgres_copy_check_query)
            check = cursor.fetchone()
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")
            print("Copy table existence: " + str(check[0] == "copy"))
            if ((check[0] == 'copy') == False and is_check):
                return CHOOSING 

def testing(update, context):
    try:
        connection = connect_db()
        cursor = connection.cursor()

        if (getText(update) == "Done"):
            # Delete record
            postgres_delete_query = """DELETE FROM check_ans WHERE user_id = %s"""
            record_to_delete = (getID(update),)
            cursor.execute(postgres_delete_query, record_to_delete)
            connection.commit()
            done(update, context)
            postgresSQL_delete_query = """DROP TABLE IF EXISTS copy"""
            cursor.execute(postgresSQL_delete_query)
            connection.commit()
            print("Table copy deleted successfully in PostgreSQL ")
            return CHOOSING
        elif (getText(update) == "/cancel"):
            # Delete record
            postgres_delete_query = """ DELETE FROM check_ans WHERE user_id = %s"""
            record_to_delete = (getID(update),)
            cursor.execute(postgres_delete_query, record_to_delete)
            connection.commit()
            cancel(update, context)
            postgresSQL_delete_query = """DROP TABLE copy"""
            cursor.execute(postgresSQL_delete_query)
            connection.commit()
            print("Table copy deleted successfully in PostgreSQL ")
            return CHOOSING
        else:
            # Find the deck_id
            postgres_deck_query = "SELECT deck_id FROM check_ans WHERE user_id = %s"
            record_to_deck = (getID(update),)
            cursor.execute(postgres_deck_query, record_to_deck)
            deck_id = cursor.fetchone()

            # Find correct ans_id
            postgres_find_query = "SELECT card_id FROM check_ans WHERE user_id = %s"
            user_id_to_select = (getID(update),)
            cursor.execute(postgres_find_query, user_id_to_select)
            card_id = cursor.fetchone()

            postgreSQL_select_query = "SELECT ans_info FROM answers WHERE ans_id = %s"
            card_to_select = card_id
            cursor.execute(postgreSQL_select_query, card_to_select)
            correct_answer = cursor.fetchone()
            user_answer = (getText(update),)
            if (user_answer[0].lower() == correct_answer[0].lower()):
                update.message.reply_text("Correct!")

                # Update number of correct attempts
                postgres_update_query = """UPDATE cards SET num_correct = num_correct + 1 WHERE card_id = %s"""
                cursor.execute(postgres_update_query, card_to_select)
                connection.commit()

                # Update score
                postgres_score_query = """UPDATE scores SET is_correct = (%s) WHERE user_id = (%s) AND qns_count IN(SELECT max(qns_count) FROM scores)"""
                score_to_insert = (True, getID(update),)
                cursor.execute(postgres_score_query, score_to_insert)
                connection.commit()

                # Delete from check_ans
                postgres_delete_query = """DELETE FROM check_ans WHERE user_id = %s"""
                record_to_delete = (getID(update),)
                cursor.execute(postgres_delete_query, record_to_delete)
                connection.commit()
                # Delete from copy
                postgresSQL_delete_query = """DELETE FROM copy WHERE card_id = %s"""
                cursor.execute(postgresSQL_delete_query, card_to_select)
                connection.commit()
                ask_qns_test(update, context, deck_id)
            else:
                # Update score
                postgres_score_query = """UPDATE scores SET is_correct = (%s) WHERE user_id = (%s) AND qns_count IN(SELECT max(qns_count) FROM scores)"""
                score_to_insert = (False, getID(update),)
                cursor.execute(postgres_score_query, score_to_insert)
                connection.commit()
                update.message.reply_text("Wrong!")
                update.message.reply_text("The answer is: {}".format(correct_answer[0]))
                # Delete from check_ans
                postgres_delete_query = """DELETE FROM check_ans WHERE user_id = %s"""
                record_to_delete = (getID(update),)
                cursor.execute(postgres_delete_query, record_to_delete)
                connection.commit()
                # Delete from copy
                postgresSQL_delete_query = """DELETE FROM copy WHERE card_id = %s"""
                cursor.execute(postgresSQL_delete_query, card_to_select)
                connection.commit()
                ask_qns_test(update, context, deck_id)
    except (Exception, psycopg2.Error) as error :
        print ("Error while fetching data from PostgreSQL", error)
    finally:
        postgres_copy_check_query = """SELECT to_regclass('copy');"""
        cursor.execute(postgres_copy_check_query)
        check = cursor.fetchone()
        if (connection):
            cursor.close()
            connection.close()
            # print("PostgreSQL connection is closed")
        print("Copy table existence: " + str(check[0] == "copy"))
        if ((check[0] == 'copy') == False):
            return CHOOSING 

def ask_qns_test(update, context, deck_id):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            # Check how many remaining questions left
            postgres_copy_count_query = """SELECT COUNT(*) FROM copy"""
            cursor.execute(postgres_copy_count_query)
            remaining = cursor.fetchone()
            # total_qns = remaining[0]
            update.message.reply_text("Remaining questions: " + str(list(remaining).pop(0)))
            if list(remaining).pop(0) == 0:

                # Count score
                postgres_total_query = """SELECT COUNT(*) FROM scores WHERE user_id = (%s)"""
                user_total = (getID(update),)
                cursor.execute(postgres_total_query, user_total)
                total_qns = cursor.fetchone()

                postgres_score_query = """SELECT COUNT(*) FROM scores WHERE user_id = (%s) AND is_correct = True"""
                user_score = (getID(update),)
                cursor.execute(postgres_score_query, user_score)
                score = cursor.fetchone()

                update.message.reply_text("You have finished the test. Good job! 👏")
                update.message.reply_text("You got {} out of {} questions correct. Nice try!".format(score[0], total_qns[0]))
                postgresSQL_delete_query = """DROP TABLE IF EXISTS copy"""
                cursor.execute(postgresSQL_delete_query)
                connection.commit()
                print("Table copy deleted successfully in PostgreSQL ")
                # Delete record
                postgres_delete_query = """DELETE FROM check_ans WHERE user_id = %s"""
                record_to_delete = (getID(update),)
                cursor.execute(postgres_delete_query, record_to_delete)
                connection.commit()

                postgres_del_query = """DELETE FROM scores WHERE user_id = %s"""
                record_to_del = (getID(update),)
                cursor.execute(postgres_del_query, record_to_del)
                connection.commit()

                return CHOOSING
            else:
                # Retrive questions from deck
                postgres_select_card_query = """SELECT card_id FROM copy
                                                ORDER BY RANDOM()
                                                LIMIT 1"""
                deck_to_select =  deck_id
                cursor.execute(postgres_select_card_query, deck_to_select)
                card_id = cursor.fetchone()
                print("Card ID: " + str(list(card_id).pop(0)))

                # Keep track of scores
                postgres_score_query = """INSERT INTO scores (user_id, deck_id, qns_count) VALUES (%s, %s, DEFAULT)"""
                score_to_insert = (getID(update), deck_id,)
                cursor.execute(postgres_score_query, score_to_insert)
                connection.commit()

                # Insert card_id that is already tested
                postgres_insert_query = """INSERT INTO check_ans (user_id, card_id, deck_id) VALUES (%s, %s, %s)"""
                record_to_insert = (getID(update), card_id, deck_id,)
                cursor.execute(postgres_insert_query, record_to_insert)
                connection.commit()

                postgres_text_query = "SELECT is_text FROM questions WHERE qns_id = %s"
                text_to_select = card_id
                cursor.execute(postgres_text_query, text_to_select)
                is_text = cursor.fetchone()[0]
                print(is_text)

                if (not is_text):
                    postgreSQL_select_query = "SELECT qns_info FROM questions WHERE qns_id = %s"
                    card_to_select = card_id
                    cursor.execute(postgreSQL_select_query, card_to_select)
                    qns = cursor.fetchone()[0]
                    update.message.reply_text("Question:\n\n")
                    chat_id = update.message.chat_id
                    context.bot.send_photo(chat_id=chat_id, photo = qns)
                    update.message.reply_text("What's the answer?")
                    # timer(update, context)
                    postgres_update_query = """UPDATE cards SET num_attempts = num_attempts + 1 WHERE card_id = %s"""
                    cursor.execute(postgres_update_query, card_to_select)
                    connection.commit()
                    print("num_attempts updated successfully")
                    # Delete card_id that is already tested from copy 
                    postgres_delete_query = """DELETE FROM copy WHERE card_id = %s"""
                    cursor.execute(postgres_delete_query, card_to_select)
                else: 
                    postgreSQL_select_query = """SELECT qns_info FROM questions WHERE qns_id = %s"""
                    card_to_select = card_id
                    cursor.execute(postgreSQL_select_query, card_to_select)
                    qns = cursor.fetchone()
                    update.message.reply_text("Question:\n\n{}".format(qns[0]))
                    update.message.reply_text("What's the answer?")
                    # timer(update, context)
                    # Update number of attempts
                    postgres_update_query = """UPDATE cards SET num_attempts = num_attempts + 1 WHERE card_id = %s"""
                    cursor.execute(postgres_update_query, card_to_select)
                    connection.commit()
                    print("num_attempts updated successfully")

                    # Delete card_id that is already tested from copy 
                    postgres_delete_query = """DELETE FROM copy WHERE card_id = %s"""
                    cursor.execute(postgres_delete_query, card_to_select)
        except (Exception, psycopg2.Error) as error :
            print ("Error while fetching data from PostgreSQL", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()

# Statistics
def stats(update, context):
    if deck_list(update, context) == 0:
        return CHOOSING
    else:
        update.message.reply_text('Which deck would you like to check?\n\n'
        'Type /cancel to stop this action and choose another option.\n\n')
        return DECK_STATS

def deck_stats(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            # Retrieve deck_id from deck_name
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            Deck_ID = cursor.fetchone()
            if Deck_ID is None:
                update.message.reply_text("This deck doesn't exist, you have to create it first! \n\nFor now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                return DECK_STATS
            deck_id_to_insert = (Deck_ID)
            # Retrieve qns_info from deck_id
            postgres_view_qns_query = """SELECT qns_info, num_attempts, num_correct, is_text FROM questions INNER JOIN cards ON questions.card_id = cards.card_id WHERE cards.deck_id = %s"""
            cursor.execute(postgres_view_qns_query, deck_id_to_insert)
            questions = cursor.fetchall()
            lst_qns = list(q[0] for q in questions)
            # print(lst_qns)
            if len(lst_qns) == 0:
                update.message.reply_text("There aren't any flashcards in this deck. \n\nAdd flashcards by clicking ADD! \n\nFor now, please type a deck with flashcards, or type /cancel to stop this action and choose another option.")
                return DECK_STATS
            lst_num_attempts = list(q[1] for q in questions)
            # print(lst_num_attempts)
            lst_num_correct = list(q[2] for q in questions)
            # print(lst_num_correct)
            lst_text = list(q[3] for q in questions)
            def get_percentage(index):
                try:
                    percentage = lst_num_correct[index]/lst_num_attempts[index] * 100
                except:
                    percentage = None
                return percentage
            def get_num_attempts(index):
                num_attempts = lst_num_attempts[index]
                return num_attempts
            def get_num_correct(index):
                num_correct = lst_num_correct[index]
                return num_correct
            def grading(percentage):
                if percentage is None:
                    update.message.reply_text("Start testing yourself with this new question!")
                elif percentage < 70:
                    update.message.reply_text("You can do better for this question. Aim for at least 70%!")
                elif percentage == 100:
                    update.message.reply_text("You aced this question! 💯")
                else: 
                    update.message.reply_text("You are doing great, keep up the good work!")
            index = 0
            for qns in lst_qns:
                if (lst_text[index]):
                    update.message.reply_text("Question {}:\n\n{}\n\nYou've attempted this question {} time(s) and got it correct {} time(s). Percentage correct: {}%".format(index + 1, qns, get_num_attempts(index), get_num_correct(index), get_percentage(index)))
                    grading(get_percentage(index))
                    index += 1
                else:
                    update.message.reply_text("Question {}:".format(index + 1))
                    chat_id = update.message.chat_id
                    context.bot.send_photo(chat_id=chat_id, photo = qns)
                    update.message.reply_text("You've attempted this question {} time(s) and got it correct {} time(s). Percentage correct: {}%".format(get_num_attempts(index), get_num_correct(index), get_percentage(index)))
                    grading(get_percentage(index))
                    index += 1
            return CHOOSING
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to check stats from the tables", error)
            return CHOOSING
        finally:
            # closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")
        
# Share decks
def share(update, context):
    reply_keyboard = [['SHARE', 'RECEIVE']]
    update.message.reply_text('Are you sharing a deck to someone, or recieving a deck from someone?\n\n'
            'Type /cancel to stop this action and choose another option.',
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SHARE_OR_RECEIVE

def share_or_receive(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    elif getText(update).lower() == "share":
        if deck_list(update, context) == 0:
            return CHOOSING
        else: 
            update.message.reply_text('Please type in the name of the deck that you want to share.\n\n'
            'Type /cancel to stop this action and choose another option.' )
            return SHARE_DECK
    elif getText(update).lower() == "receive":
        update.message.reply_text('Please type in the token shared by the person sharing their deck.\n\n'
        'Type /cancel to stop this action and choose another option.')
        return RECEIVE_DECK
    else:
        return CHOOSING

def share_deck(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()

            # Retrieve deck_id from deck_name
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                update.message.reply_text("This deck doesn't exist, you have to create it first! \n\nFor now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                return SHARE_DECK
            print(DECK_ID)
            update.message.reply_text('Your special token for deck {} is {}. \n\nPlease send this token to the person who you are sharing the deck to. Make sure that they do not have an existing deck with the same name.'.format(getText(update), DECK_ID[0] + random_no),
                                    reply_markup=markup)
            return CHOOSING
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to share decks: ", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")  

def is_int(n):
    try: 
        int(n)
        return True
    except ValueError:
        return False

def receive_deck(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()

            if (not is_int):
                update.message.reply_text('Please type in only the token shared by the person sharing their deck. \n\n'
                                    'Type /cancel to stop this action and choose another option.')
                return RECEIVE_DECK

            old_deck_id = int(getText(update)) - random_no
            print(old_deck_id)


            # Get deck name
            postgres_card_query = """SELECT deck_name FROM decks WHERE deck_id = (%s)"""
            deck_to_insert = (old_deck_id,)
            cursor.execute(postgres_card_query, deck_to_insert)
            deck_name = cursor.fetchone()
            print(deck_name)


            # Check if deck_name already existed
            postgres_search_query = """SELECT COUNT(*) FROM decks WHERE deck_name = %s AND user_id = %s"""
            deck_to_insert = (deck_name, getID(update),)
            cursor.execute(postgres_search_query, deck_to_insert)
            CHECK = cursor.fetchone()
            if CHECK[0] == 0:
                # Insert deck
                postgres_insert_query = """INSERT INTO decks (deck_id, deck_name, user_id) VALUES (DEFAULT, %s, %s)"""
                cursor.execute(postgres_insert_query, deck_to_insert)
                connection.commit()
                count = cursor.rowcount
                print (count, "deck inserted successfully into decks table")
            else:
                update.message.reply_text("You already have a deck called {}. Unable to recieve this deck. Please rename your existing deck named {}".format(deck_name[0], deck_name[0]), reply_markup = markup)
                return CHOOSING

            update.message.reply_text("Sharing decks... (This might take a while)")


            postgres_new_deck_query = """SELECT deck_id FROM decks WHERE deck_name = %s AND user_id = %s"""
            new_deck = (deck_name, getID(update),)
            cursor.execute(postgres_new_deck_query, new_deck)
            deck_id = cursor.fetchone()
            print(deck_id)


            create_temp_cards_query = '''SELECT * FROM cards WHERE cards.deck_id = %s'''
            temp_cards_query = (old_deck_id,)
            cursor.execute(create_temp_cards_query, temp_cards_query)
            connection.commit()
            print("tamp cards created")
            cards = cursor.fetchall()
            print(cards)

            for c in cards:
                postgres_insert_query = """INSERT INTO cards (card_id, deck_id, qns_id, ans_id, num_attempts, num_correct) VALUES (DEFAULT, %s, DEFAULT, DEFAULT, 0, 0)"""
                card_to_insert = (deck_id,)
                cursor.execute(postgres_insert_query, card_to_insert)
                connection.commit()
                print(c)
            print("cards table updated")


            create_temp_qns_query = '''SELECT * from questions INNER JOIN cards ON questions.card_id = cards.card_id WHERE cards.deck_id = %s'''
            temp_qns_query = (old_deck_id,)
            cursor.execute(create_temp_qns_query, temp_qns_query)
            connection.commit()
            print("tamp qns created")
            qns = cursor.fetchall()
            print(qns)

            for q in qns:
                postgres_insert_query = """INSERT INTO questions (qns_id, card_id, qns_info, is_text) VALUES (DEFAULT, DEFAULT, %s, %s)"""
                question_to_insert = (q[2], q[3],)
                cursor.execute(postgres_insert_query, question_to_insert)
                connection.commit()
            print("qns table updated")


            create_temp_ans_query = '''SELECT * from answers INNER JOIN cards ON answers.card_id = cards.card_id WHERE cards.deck_id = %s'''
            temp_ans_query = (old_deck_id,)
            cursor.execute(create_temp_ans_query, temp_ans_query)
            connection.commit()
            print("tamp ans created")
            ans = cursor.fetchall()
            print(ans)

            for a in ans:
                postgres_insert_query = """INSERT INTO answers (ans_id, card_id, ans_info) VALUES (DEFAULT, DEFAULT, %s)"""
                answer_to_insert = (a[2],)
                cursor.execute(postgres_insert_query, answer_to_insert)
                connection.commit()
            print("ans table updated")



            update.message.reply_text("{} deck successfully shared! Choose VIEW to see more details.".format(deck_name[0]), reply_markup = markup)
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to share decks: ", error)
                update.message.reply_text("This deck doesn't exist! There might have been a typo. Please try again.", reply_markup = markup)
                return CHOOSING
        finally:
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")
            return CHOOSING

# Rename
def rename(update, context):
    if deck_list(update, context) == 0:
        return CHOOSING
    else:
        update.message.reply_text(
        'Which deck would you like to rename?\n\n'
        'Type /cancel to stop this action and choose another option.\n\n')
        return DECK_TO_RENAME

def deck_to_rename(update, context):
    print("renaming deck...")
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()

            # Retrieve deck_id from deck_name
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            deck_name_and_id = (getText(update), getID(update),)
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                update.message.reply_text("This deck doesn't exist, you have to create it first! \n\nFor now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                return DECK_TO_RENAME
            print("deck found")
            print(DECK_ID)

            postgres_update_query = """UPDATE decks SET deck_name = 'HOPEFULLYNOBODYUSESTHISDECKNAMEIDK' WHERE deck_id = %s"""
            cursor.execute(postgres_update_query, DECK_ID)
            connection.commit()
            print("deck updated successfully")

            update.message.reply_text("What would you like to rename {} deck as?".format(getText(update)))
            return RENAME_DECK
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to insert card into cards table: ", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")

def rename_deck(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()

            # Check if deck_name already existed
            postgres_search_query = """SELECT COUNT(*) FROM decks WHERE deck_name = %s AND user_id = %s"""
            deck_to_insert = (getText(update), getID(update),)
            cursor.execute(postgres_search_query, deck_to_insert)
            CHECK = cursor.fetchone()
            if CHECK[0] == 0:


                # Retrieve deck_id from deck_name
                postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = %s AND user_id = (%s)"""
                deck_name_and_id = ("HOPEFULLYNOBODYUSESTHISDECKNAMEIDK", getID(update),)
                cursor.execute(postgres_deck_id_query, deck_name_and_id)
                DECK_ID = cursor.fetchone()
                print("deck to change found")
                print(DECK_ID[0])


                # Delete deck
                postgres_delete_deck_query = """UPDATE decks SET deck_name = (%s) WHERE deck_id = (%s)"""
                deck_to_delete = (getText(update), DECK_ID[0],)
                cursor.execute(postgres_delete_deck_query, deck_to_delete)
                connection.commit()
                print ("deck_name_updated")

                update.message.reply_text("Deck successfully renamed to {}.".format(getText(update)), reply_markup = markup)
                return CHOOSING
            else:
                update.message.reply_text("You already have a deck called {}. Please type in another name, or type /cancel to stop this action and choose another option. ".format(getText(update)))
                return RENAME_DECK

        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to delete deck from decks table", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")

""" Other functions """
# Cancel current actions
def cancel(update, context):
    update.message.reply_text("Action is cancelled successfully.", reply_markup=markup)
    return CHOOSING

# Provides user details of all commands
def help(update, context):
    helpMessage = "Available commands to choose from:\n\n"
    helpMessage += "/start - start using below features\n\n"

    helpMessage += "First page:\n"
    helpMessage += "NEW 🆕 - create a new deck\n"
    helpMessage += "VIEW 👀 - view all created decks, and all flashcards within\n"
    helpMessage += "ADD ➕ - add flashcards to a deck\n"
    helpMessage += "DELETE ⛔ - delete decks or individual flashcards\n"
    helpMessage += "PRACTICE 💪 - practice with selected deck (unlimited tries and /skip command)\n"
    helpMessage += "TEST ✍ - test yourself with selected deck (only 1 try per question)\n"
    helpMessage += "STATS 📊 - view accuracy statistics of questions in a selected deck\n"
    helpMessage += "NEXT ➡️ - go to next page of keyboard buttons\n\n"

    helpMessage += "Second page:\n"
    helpMessage += "SHARE 📩 - share your created decks or recieve shared decks from others\n"
    helpMessage += "RENAME ✏️ - rename a selected deck\n"
    helpMessage += "SET TEST TIMER ⏱️ - set or unset a timer\n"
    helpMessage += "MOTIVATIONAL QUOTES 😉 - get a random motivational quote\n"
    helpMessage += "DAILY REMINDER 🔔 - set a daily reminder for yourself at a selected time\n"
    helpMessage += "POMODORO TIMER 🍅 - productivity timer to to help you focus on work (25 mins)\n"
    helpMessage += "BACK ⬅️ - go to previous page of keyboard buttons\n"
    helpMessage += "RESTART BOT 🆘 - restart the bot\n\n"

    helpMessage += "Additional commands:\n"
    helpMessage += "/help - view all commands and what they do\n"
    
    update.message.reply_text(helpMessage)
    return CHOOSING

# Retrieve user_id
def getID(update):
    return(update.message.chat.id)

# Retrieve user's response
def getText(update):
    return(update.message.text)

# Restart bot
def done(update, context):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        # Delete record
        postgres_delete_query = """DELETE FROM check_ans WHERE user_id = %s"""
        record_to_delete = (getID(update),)
        cursor.execute(postgres_delete_query, record_to_delete)
        connection.commit()
        postgresSQL_delete_query = """DROP TABLE IF EXISTS copy """
        cursor.execute(postgresSQL_delete_query)
        connection.commit()
        postgresSQL_delete_query = """DROP TABLE IF EXISTS index """
        cursor.execute(postgresSQL_delete_query)
        connection.commit()
        print("Table copy deleted successfully in PostgreSQL ")

    except (Exception, psycopg2.Error) as error :
        print ("Error while fetching data from PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()
            # print("PostgreSQL connection is closed")
        update.message.reply_text("Type /start to start again!")
        return ConversationHandler.END

# Generate a random quote
def quotes(update, context):
    arr = ["Keep up the good work!", "You got this!", "You're doing great!", "You can do it!"]
    rand = random.randint(0,3)
    update.message.reply_text(get_random_quote())
    update.message.reply_text(arr[rand])
    return CHOOSING

# Reminders
def daily_reminder(update, context):
    reply_keyboard = [['SET', 'UNSET']]
    update.message.reply_text('Are you setting or unsetting daily reminder?\n\n'
                                'Type /cancel to stop this action and choose another option.',
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SET_OR_UNSET

def set_or_unset(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    elif getText(update).lower() == "set":
        setreminder(update, context)
    elif getText(update).lower() == "unset":
        stopreminder(update, context)
    else:
        return CHOOSING

def callback_alarm(context: CallbackContext):
    context.bot.send_message(chat_id=context.job.context, text='Remember to practice your flashcards!')

def setreminder(update, context: CallbackContext):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='Reminder has been set! A reminder will be sent every day at this time!',
                             reply_markup = markup)
    # t = datetime.datetime.now(datetime.timezone.utc)
    # t1 = datetime.datetime.now()
    # t = t1.astimezone(pytz.timezone('Asia/Singapore'))
    # context.job_queue.run_daily(callback_alarm, context=update.message.chat_id, days=(0, 1, 2, 3, 4, 5, 6), time = t)
    context.job_queue.enabled = True 
    context.job_queue.start()
    context.job_queue.run_repeating(callback_alarm, context=update.message.chat_id, interval=86400, first=0)
    return CHOOSING

def stopreminder(update, context: CallbackContext):
    #if (not context.job_queue.enabled):
    #    context.bot.send_message(chat_id=update.message.chat_id,
    #                         text='No daily reminders have been set yet!',
    #                         reply_markup = markup)
    #else:
    context.bot.send_message(chat_id=update.message.chat_id,
                            text='Daily reminders have been cancelled!',
                            reply_markup = markup)
    context.job_queue.enabled = False 
    context.job_queue.stop()
    return CHOOSING

# Menu Keyboard
def next(update, context):
    update.message.reply_text("Go to second page of commands...", reply_markup = markup_2)
    return CHOOSING

def back(update, context):
    update.message.reply_text("Back to first page of commands...", reply_markup = markup)
    return CHOOSING

# Pomodoro Timer
def pomodoro_timer(update, context):
    reply_keyboard = [['START']]
    update.message.reply_text('Want to be more productive? Click START and focus on your tasks while the time is not up!\n\n'
                            'Type /cancel to stop this action and choose another option.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return START_POMODORO

def alarm(context):
    job = context.job
    context.bot.send_message(job.context, text='Beep!')

def start_pomodoro(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    elif getText(update).lower() == "start":
        chat_id = update.message.chat_id
        duration = 25 * 60
        time_left = duration
        update.message.reply_text('25 minutes starts now!')
        for i in range(duration):
            time.sleep(1)
            time_left = time_left - i
        reply_keyboard_2 = [['SHORT BREAK', 'LONG BREAK']]
        update.message.reply_text('Time to take a rest!\nDo you want to take a short break (5 mins) or a long break(15 mins)?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard_2, one_time_keyboard=True))
        return REST_POMODORO

def start_again_pomodoro(update, context):
    chat_id = update.message.chat_id
    duration = 25 * 60
    new_job = context.job_queue.run_once(alarm, duration, context=chat_id)
    update.message.reply_text('25 minutes starts now!')
    for i in range(duration):
        time.sleep(1)
    reply_keyboard = [['SHORT BREAK', 'LONG BREAK']]
    update.message.reply_text('Time to take a rest!\nDo you want to take a short break (5 mins) or a long break(15 mins)?',
    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return REST_POMODORO

def rest_pomodoro(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    elif getText(update).lower() == "short break":
        chat_id = update.message.chat_id
        duration = 5 * 60 
        new_job = context.job_queue.run_once(alarm, duration, context=chat_id)
        update.message.reply_text('5 minutes starts now!')
        for i in range(duration):
            time.sleep(1)
        update.message.reply_text('Rest time is up!')
        reply_keyboard = [['START AGAIN', 'QUIT']]
        update.message.reply_text('Do you want to start the pomodoro timer again or quit?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return START_OR_QUIT
    elif getText(update).lower() == "long break":
        chat_id = update.message.chat_id
        duration = 15 * 60 
        new_job = context.job_queue.run_once(alarm, duration, context=chat_id)
        update.message.reply_text('5 minutes starts now!')
        for i in range(duration):
            time.sleep(1)
        update.message.reply_text('Rest time is up!')
        reply_keyboard = [['START AGAIN', 'QUIT']]
        update.message.reply_text('Do you want to start the pomodoro timer again or quit?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return START_OR_QUIT

def start_or_quit(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    elif getText(update).lower() == "start again":
        return start_again_pomodoro(update, context)
    elif getText(update).lower() == "quit":
        update.message.reply_text("Alright, let\'s stop. Keep up the good work!",reply_markup = markup)
        return CHOOSING

# Timer
def timer(update, context):
    update.message.reply_text("How long do you want your timer to be? (in minutes)\nClick /cancel if you do not want to start a timer. ")
    return CHOOSE_TIME

def alarm(context):
    """Send the alarm message."""
    job = context.job
    context.bot.send_message(job.context, text='Your time is up!')

def set_timer(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        chat_id = update.message.chat_id
        try:
            duration = int(getText(update))
            due = duration * 60
            print(due)
            if due < 0:
                update.message.reply_text('Invalid value! Try again.')
                return CHOOSE_TIME
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()
            new_job = context.job_queue.run_once(alarm, due, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text('Timer set successfully!')
            update.message.reply_text("Duration of timer: {} minutes".format(duration))
        except (IndexError, ValueError):
            update.message.reply_text('Usage: <Integer greater than 0>')

def unset(update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        update.message.reply_text('You have no active timer')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Timer successfully unset!')

# Log Errors caused by Updates.
def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("help", help))
    conv_handler_normal = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^NEW 🆕$'), new),
                MessageHandler(Filters.regex('^ADD ➕$'), add),
                MessageHandler(Filters.regex('^DELETE ⛔$'), delete),
                MessageHandler(Filters.regex('^VIEW 👀$'), view_deck),
                MessageHandler(Filters.regex('^TEST ✍$'), test),
                MessageHandler(Filters.regex('^PRACTICE 💪$'), practice),
                MessageHandler(Filters.regex('^NEXT ➡️$'), next),
                MessageHandler(Filters.regex('^BACK ⬅️$'), back),
                MessageHandler(Filters.regex('^STATS 📊$'), stats),
                MessageHandler(Filters.regex('^RENAME ✏️$'), rename),
                MessageHandler(Filters.regex('^SHARE 📩$'), share),
                MessageHandler(Filters.regex('^RESTART BOT 🆘$'), done),
                MessageHandler(Filters.regex('^MOTIVATIONAL QUOTES 😉$'), quotes),
                MessageHandler(Filters.regex('^DAILY REMINDER 🔔$'), daily_reminder),
                MessageHandler(Filters.regex('^POMODORO TIMER 🍅$'), pomodoro_timer),
                MessageHandler(Filters.regex('^SET TIMER ⏱️$'), timer),
            ],
            CREATE_DECK: [MessageHandler(Filters.text, create_deck)
            ],
            CHOOSE_DELETE: [MessageHandler(Filters.text, choose_delete)
            ],
            DELETE_DECK: [MessageHandler(Filters.text, delete_deck)
            ],
            SHOW_QNS: [MessageHandler(Filters.text, show_qns)
            ],
            DELETE_QNS: [MessageHandler(Filters.text, delete_qns)
            ],
            INSERT_CARD: [MessageHandler(Filters.text, insert_card)
            ],
            VIEW_QNA: [MessageHandler(Filters.text, view_qna)
            ],
            CHOOSE_TYPE: [MessageHandler(Filters.text, choose_type)
            ],
            ADD_QNS_TEXT: [MessageHandler(Filters.text, add_qns)
            ],
            ADD_QNS_PHOTO:[MessageHandler(Filters.photo, get_photo)
            ],
            ADD_ANS: [MessageHandler(Filters.text, add_ans)
            ],
            ADD_MORE_QNS: [MessageHandler(Filters.text, add_more_qns)
            ],
            DECK_TEST: [MessageHandler(Filters.text, deck_test)
            ],
            DECK_TEST_TEST: [MessageHandler(Filters.text, deck_test_test)
            ],
            PRACTICING: [MessageHandler(Filters.text, practicing)
            ],
            TESTING: [MessageHandler(Filters.text, testing)
            ],
            DECK_STATS: [MessageHandler(Filters.text, deck_stats)
            ],
            SHARE_OR_RECEIVE: [MessageHandler(Filters.text, share_or_receive),
            ],
            SHARE_DECK: [MessageHandler(Filters.text, share_deck),
            ],
            RECEIVE_DECK: [MessageHandler(Filters.text, receive_deck),
            ],
            DECK_TO_RENAME: [MessageHandler(Filters.text, deck_to_rename),
            ], 
            RENAME_DECK: [MessageHandler(Filters.text, rename_deck),
            ],
            DECK_STATS: [MessageHandler(Filters.text, deck_stats),
            ],
            SET_OR_UNSET: [MessageHandler(Filters.text, set_or_unset),
            ],
            START_POMODORO: [MessageHandler(Filters.text, start_pomodoro),
            ],
            START_AGAIN_POMODORO: [MessageHandler(Filters.text, start_again_pomodoro),
            ],
            REST_POMODORO: [MessageHandler(Filters.text, rest_pomodoro),
            ],
            START_OR_QUIT: [MessageHandler(Filters.text, start_or_quit),
            ],
            CHOOSE_TIME: [MessageHandler(Filters.text, set_timer),
            ],
        },
        fallbacks = [CommandHandler('Done', done)]
    )
    dp.add_handler(conv_handler_normal)
    dp.add_error_handler(error)
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://memoize-me-telegram-bot.herokuapp.com/' + TOKEN)
    updater.idle()

if __name__ == '__main__':
    main()
