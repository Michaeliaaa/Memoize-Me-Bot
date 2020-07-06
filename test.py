import logging
from telegram.ext import (Updater, InlineQueryHandler, CommandHandler,  CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext)
from telegram.ext.dispatcher import run_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import requests
import re
import psycopg2
from psycopg2 import Error
from quotes import get_random_quote
from random import randint
import logging
import os
import math
from datetime import time

PORT = int(os.environ.get('PORT', 5000))
TOKEN = "1257761341:AAEL0eO8n4kgvSy3CfJgAAg4EkaME4JQ5sM"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, CREATE_DECK, CHOOSE_DELETE, DELETE_DECK, SHOW_QNS, DELETE_QNS, INSERT_CARD, VIEW_QNA, ADD_QNS, ADD_ANS, ADD_MORE_QNS, DECK_TEST, DECK_TEST_TEST, PRACTICING, TESTING, DONE = range(16)

reply_keyboard = [['NEW 🆕', 'VIEW 👀'],
                  ['ADD ➕', 'DELETE ➖'],
                  ['PRACTICE 💪', 'TEST ✍'],
                  ['DONE ✅']]
markup = ReplyKeyboardMarkup(reply_keyboard)

# Connect to db
def connect_db():
        connection = psycopg2.connect(user = "ypuzvnpikuyzec",
                                  password = "b508ea454fb3ea5f4831560152799b203714bc742bb8c4b000fac6b91ef28cec",
                                  host = "ec2-35-171-31-33.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "dfhns0og19dacd")
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

# Command to create a new deck 
def new(update, context):
    update.message.reply_text(
        '\nLet\'s create a new deck of flashcards!\n'
        'Type /cancel to stop this action and choose another option.\n\n'
        'Please give your new deck a name.')
    return CREATE_DECK

# Store the deck into the database.
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
                update.message.reply_text("You already had a deck called {}. Please try another name. \n\n Type /cancel to stop this action and choose another option.".format(getText(update)))
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

# Command to view user's decks
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
            update.message.reply_text("You don't have any decks right now.\nClick NEW to create your first deck!")
            return CHOOSING
        else:
            str = "Here are all the decks you\'ve created:\n"
            for i in lst_of_decks:
                str = str + i + "\n"
            update.message.reply_text(str)
            update.message.reply_text(
            '\nWhich deck would you like to look into?\n'
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

# View user's question of chosen deck
def view_qna(update, context):
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
                update.message.reply_text("This deck doesn't exist, you have to create it first! For now, please type an existing deck, or type /cancel to stop this action and choose another option.")
            deck_id_to_insert = (DECK_ID)
            # Retrieve qns_info from deck_id
            postgres_view_qns_query = """SELECT qns_info FROM questions INNER JOIN cards ON questions.card_id = cards.card_id WHERE cards.deck_id = %s"""
            cursor.execute(postgres_view_qns_query, deck_id_to_insert)
            questions = cursor.fetchall()
            lst_of_qns = list(q[0] for q in questions)
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
                    update.message.reply_text(("Question {}: \n\n" + i).format(str(index)))
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
                return CHOOSING

# Return a list of the user's decks
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
            update.message.reply_text("You don't have any decks right now.\nClick NEW to create your first deck!")
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

# Command to create a new card 
def add(update, context):
    update.message.reply_text(
        '\nLet\'s create a new flashcard!\n'
        'Type /cancel to stop this action and choose another option.\n\n')
    update.message.reply_text("Which deck would you like to add a flashcard to?")
    if deck_list(update, context) == 0:
        return CHOOSING
    return INSERT_CARD

# Store the card into the database.
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
                update.message.reply_text("This deck doesn't exist, you have to create it first! For now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                return INSERT_CARD
            # Insert card
            postgres_insert_query = """INSERT INTO cards (card_id, deck_id, qns_id, ans_id) VALUES (DEFAULT, %s, DEFAULT, DEFAULT)"""
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
            update.message.reply_text("Please type in your question.")
            return ADD_QNS
        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to insert card into cards table: ", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")

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
            postgres_insert_query = """INSERT INTO questions (qns_id, card_id, qns_info) VALUES (DEFAULT, DEFAULT, %s)"""
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
            update.message.reply_text("Flashcard succesfully added.")
            #                     reply_markup=markup)
            # reply_keyboard = [['Yes', 'No']]
            # update.message.reply_text("Would you like add more flashcards?",
            #                     reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            update.message.reply_text("Would you like add more flashcards to this deck?\n\nType YES to continue and type NO to stop and choose another action.")
            return ADD_MORE_QNS
            #return CHOOSING

def add_more_qns(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    elif getText(update).lower() == "yes":
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
            return ADD_QNS

        except (Exception, psycopg2.Error) as error :
            if (connection):
                print("Failed to add more question", error)
        finally:
            # closing database connection.
            if (connection):
                cursor.close()
                connection.close()

    elif getText(update).lower() == "no":
        print("Add more: No")
        update.message.reply_text("Alright, no more flashcard will be added.")
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
            postgres_insert_query = """INSERT INTO cards (card_id, deck_id, qns_id, ans_id) VALUES (DEFAULT, %s, DEFAULT, DEFAULT)"""
            card_to_insert = (deck_id,)
            cursor.execute(postgres_insert_query, card_to_insert)
            connection.commit()
            count = cursor.rowcount
            
            postgres_score_query = """INSERT INTO scores (user_id, deck_id, qns_count) VALUES (%s, %s, DEFAULT)"""
            score_to_insert = (getID(update), deck_id,)
            cursor.execute(postgres_score_query, score_to_insert)
            connection.commit()

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
                # print("PostgreSQL connection is closed")

# Command to either delete user's decks or questions (?)
def delete(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else: 
        update.message.reply_text(
            'If you would like to delete an entire deck, type DECK.\n\n'
            'If you would like to delete a question from a specific deck, type QNS.\n\n'
            'Type /cancel to stop this action and choose another option.')
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
        update.message.reply_text("Type either DECK or QNS, or type /cancel to stop this action and choose another option.")
        return CHOOSE_DELETE
        
def delete_deck(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
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
        except (Exception, psycopg2.Error) as error :
            if(connection):
                print("Failed to delete deck from decks table", error)
        finally:
            # closing database connection.
            if (connection):
                cursor.close()
                connection.close()
                # print("PostgreSQL connection is closed")
            update.message.reply_text("{} succesfully deleted.".format(getText(update)),
                                reply_markup=markup)
            return CHOOSING  

def show_qns(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
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
            # Retrieve deck_id from deck_name
            postgres_deck_id_query = """SELECT deck_id FROM decks WHERE deck_name = (%s) AND user_id = (%s)"""
            cursor.execute(postgres_deck_id_query, deck_name_and_id)
            DECK_ID = cursor.fetchone()
            if DECK_ID is None:
                update.message.reply_text("This deck doesn't exist, you have to create it first! For now, please type an existing deck, or type /cancel to stop this action and choose another option.")
            deck_id_to_insert = (DECK_ID)
            # Retrieve qns_id from deck_id
            postgres_qns_id_query = """SELECT qns_id FROM cards WHERE cards.deck_id = %s"""
            cursor.execute(postgres_qns_id_query, deck_id_to_insert)
            ids = cursor.fetchall()
            print("Qns IDs: " + str(ids))
            # Retrieve qns_info from deck_id
            postgres_view_qns_query = """SELECT qns_info FROM questions INNER JOIN cards ON questions.card_id = cards.card_id WHERE cards.deck_id = %s"""
            cursor.execute(postgres_view_qns_query, deck_id_to_insert)
            questions = cursor.fetchall()
            lst_of_qns = list(q[0] for q in questions)
            if len(lst_of_qns) == 0:
                update.message.reply_text("There aren't any flashcards in this deck.\n\nAdd flashcards by clicking ADD!")
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
                     update.message.reply_text("Question {}: ".format(str(qns_no)) + qns)
                     qns_no = qns_no + 1
                update.message.reply_text('Please type the question number of the question that you would like to delete.')
                update.message.reply_text('For multiple deletion, please use comma to separate the question.')
                return DELETE_QNS
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
    
def delete_qns(update, context):
    if (getText(update) == "/cancel"):
        cancel(update, context)
        return CHOOSING
    else:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            # Retrieve qns_id from index
            postgres_select_query = """SELECT qns_id FROM index WHERE qns_index = %s"""
            qns_index_to_insert = (getText(update),)
            cursor.execute(postgres_select_query, qns_index_to_insert)
            CARD_ID = cursor.fetchone()
            # Delete card
            postgres_delete_card_query = """DELETE FROM cards WHERE card_id = %s"""
            cursor.execute(postgres_delete_card_query, CARD_ID)
            connection.commit()
            print ("card {} deleted successfully from cards table".format(CARD_ID))
            # Delete question
            postgres_delete_qns_query = """DELETE FROM questions WHERE card_id = %s"""
            cursor.execute(postgres_delete_qns_query, CARD_ID)
            connection.commit()
            print ("question {} deleted successfully from questions table".format(CARD_ID))
            # Delete answer
            postgres_delete_ans_query = """DELETE FROM answers WHERE card_id = %s"""
            cursor.execute(postgres_delete_ans_query, CARD_ID)
            connection.commit()
            print ("answer {} deleted successfully from answers table".format(CARD_ID))
            update.message.reply_text('Selected flashcard has been deleted successfully.')
            # Delete index table
            postgresSQL_delete_query = """DROP TABLE index"""
            cursor.execute(postgresSQL_delete_query)
            connection.commit()
            print("Table index deleted successfully in PostgreSQL ")
            return CHOOSING
        except (Exception, psycopg2.Error) as error :
            postgresSQL_delete_query = """DROP TABLE index"""
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

def practice(update, context):
    update.message.reply_text(
        'Practice makes perfect! 👍\n'
        'Type /cancel to stop this action or want to stop and choose another option.\n\n')
    if deck_list(update, context) == 0:
        return CHOOSING
    else:
        update.message.reply_text("Which deck would you like to practice?")
        return DECK_TEST

def deck_test(update, context):
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
                update.message.reply_text("This deck doesn't exist, you have to create it first! For now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                return DECK_TEST
            else:
                postgres_card_query = """SELECT card_id FROM cards WHERE deck_id = (%s)"""
                #check_card_in_deck = (DECK_ID)
                cursor.execute(postgres_card_query, DECK_ID)
                iscards = cursor.fetchone()
                if iscards is None:
                    update.message.reply_text("There aren't any flashcards in this deck! Click ADD to start adding flashcards! For now, please type a deck with flashcards, or type /cancel to stop this action and choose another option.")
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
            if ((check[0] == 'copy') == False):
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
                postgresSQL_delete_query = """DROP TABLE copy"""
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
            postgresSQL_delete_query = """DROP TABLE copy IF EXISTS"""
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
            update.message.reply_text("The answer is: \n\n{}".format(correct_answer[0]))
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
    update.message.reply_text(
        'Time for test! Good luck 🍀!\n'
        'Type /cancel to stop this action or want to stop and choose another option.\n\n')
    update.message.reply_text("Which deck would you like to be tested on?")
    if deck_list(update, context) == 0:
        return CHOOSING
    return DECK_TEST_TEST

def deck_test_test(update, context):
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
                update.message.reply_text("This deck doesn't exist, you have to create it first! For now, please type an existing deck, or type /cancel to stop this action and choose another option.")
                return DECK_TEST_TEST
            else:
                postgres_card_query = """SELECT card_id FROM cards WHERE deck_id = (%s)"""
                #check_card_in_deck = (DECK_ID)
                cursor.execute(postgres_card_query, DECK_ID)
                iscards = cursor.fetchone()
                if iscards is None:
                    update.message.reply_text("There aren't any flashcards in this deck! Click ADD to start adding flashcards! For now, please type a deck with flashcards, or type /cancel to stop this action and choose another option.")
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
                postgresSQL_delete_query = """DROP TABLE copy"""
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

                postgreSQL_select_query = "SELECT qns_info FROM questions WHERE qns_id = %s"
                card_to_select = card_id
                cursor.execute(postgreSQL_select_query, card_to_select)
                qns = cursor.fetchone()
                update.message.reply_text("Question:\n\n{}".format(qns[0]))
                update.message.reply_text("What's the answer?")

                # Delete card_id that is already tested from copy 
                postgres_delete_query = """DELETE FROM copy WHERE card_id = %s"""
                cursor.execute(postgres_delete_query, card_to_select)
        except (Exception, psycopg2.Error) as error :
            print ("Error while fetching data from PostgreSQL", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()

def testing(update, context):
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
            postgresSQL_delete_query = """DROP TABLE copy IF EXISTS"""
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

""" Other functions """
# Cancel current actions
def cancel(update, context):
    update.message.reply_text("Action is cancelled successfully.")
    return CHOOSING

# Provides user details of all commands
def help(update, context):
    helpMessage = "Available commands to choose from:\n\n"
    helpMessage += "START - start using below features\n"
    helpMessage += "NEW - create new deck\n"
    helpMessage += "ADD - add flashcards to deck\n"
    helpMessage += "DELETE - delete decks\n"
    helpMessage += "VIEW - view all created decks\n"
    helpMessage += "PRACTICE - practice with selected deck\n"
    helpMessage += "TEST - test yourself with selected deck\n"
    helpMessage += "/quotes - get a motivational quote\n"
    helpMessage += "/reminder - set a daily reminder for yourself at this time\n"
    helpMessage += "/stopreminder - stop daily reminder\n"
    helpMessage += "/set <seconds> - set a timer\n"
    helpMessage += "/unset - unset the timer\n"
    helpMessage += "/stats - test statistics (for now DONE)\n"
    update.message.reply_text(helpMessage)
    return CHOOSING

# Retrieve user_id
def getID(update):
    return(update.message.chat.id)

# Retrieve user's response
def getText(update):
    return(update.message.text)

# change this to cancel?
def done(update, context):
    update.message.reply_text("That's all for today! Type /start to start again!")
    return ConversationHandler.END

# Generate a random quote
def quotes(update, context):
    update.message.reply_text(get_random_quote())

# Send reminder to practice
def callback_alarm(context: CallbackContext):
    context.bot.send_message(chat_id=context.job.context, text='Remember to practice your flashcards!')

def callback_timer(update, context: CallbackContext):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='Reminder has been set! A reminder will be sent every day at this time!')

    #context.job_queue.run_daily(callback_alarm, context=update.message.chat_id, days=(0, 1, 2, 3, 4, 5, 6), time = time(hour = 10, minute = 00, second = 00))
    context.job_queue.enabled = True 
    context.job_queue.start()
    context.job_queue.run_repeating(callback_alarm, context=update.message.chat_id, interval=86400, first=0)

# Stop daily reminders
def stopreminder(update, context: CallbackContext):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='Daily reminders have been cancelled!')
    context.job_queue.enabled = False 
    context.job_queue.stop()

# Tell user that ime is up
def alarm(context):
    """Send the alarm message."""
    job = context.job
    context.bot.send_message(job.context, text='Your time is up!')

# Set timer
def set_timer(update, context):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = int(context.args[0])
        if due < 0:
            update.message.reply_text('Sorry we can not go back to future!')
            return
        # Add job to queue and stop current one if there is a timer already
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        new_job = context.job_queue.run_once(alarm, due, context=chat_id)
        context.chat_data['job'] = new_job
        update.message.reply_text('Timer set successfully!')
        minutes = math.floor(due/60)
        seconds = due % 60
        update.message.reply_text("Duration of timer: {} minutes and {} seconds".format(minutes, seconds))
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <seconds>')

# Unset timer
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
    dp.add_handler(CommandHandler("quotes", quotes))
    remind_handler = CommandHandler('reminder', callback_timer)
    dp.add_handler(remind_handler)
    dp.add_handler(CommandHandler("stopreminder", stopreminder))
    dp.add_handler(CommandHandler("set", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^NEW 🆕$'), new),
                MessageHandler(Filters.regex('^ADD ➕$'), add),
                MessageHandler(Filters.regex('^DELETE ➖$'), delete),
                MessageHandler(Filters.regex('^VIEW 👀$'), view_deck),
                MessageHandler(Filters.regex('^TEST ✍$'), test),
                MessageHandler(Filters.regex('^PRACTICE 💪$'), practice),
                MessageHandler(Filters.regex('^DONE ✅$'), done)
            ],
            CREATE_DECK: [
                MessageHandler(Filters.text, create_deck)
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
            ADD_QNS: [MessageHandler(Filters.text, add_qns)
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
            ]
        },
        fallbacks = [CommandHandler('Done', done)]
    )
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    # updater.start_webhook(listen="0.0.0.0",
    #                       port=int(PORT),
    #                       url_path=TOKEN)
    # updater.bot.setWebhook('https://memoize-me-telegram-bot.herokuapp.com/' + TOKEN)
    updater.idle()

if __name__ == '__main__':
    main()
