# DB connection
import psycopg2
from psycopg2 import Error

try:
    connection = psycopg2.connect(user = "jhfdzctgeytrkt",
                                  password = "6f0913d556bf6eee840e0e2ba8b4c0b3ef0331f6855852008be07eeb840cdb6f",
                                  host = "ec2-35-173-94-156.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "dbpduk6f0fbp8q")

    cursor = connection.cursor()
    
    create_users_table_query = '''CREATE TABLE IF NOT EXISTS users
          (user_id INT PRIMARY KEY); '''
    cursor.execute(create_users_table_query)
    connection.commit()
    print("Table users created successfully in PostgreSQL ")


    create_decks_table_query = '''CREATE TABLE IF NOT EXISTS decks
          (deck_id INT PRIMARY KEY,
          deck_name TEXT NOT NULL,
          user_id  INT  NOT NULL,
          card_id  INT);'''
          #FOREIGN KEY (user_id) REFERENCES users (user_id)); '''
    cursor.execute(create_decks_table_query)
    connection.commit()
    print("Table decks created successfully in PostgreSQL ")


    create_cards_table_query = '''CREATE TABLE IF NOT EXISTS cards
          (card_id INT PRIMARY KEY,
          deck_id INT,
          qns_id  INT,
          ans_id  INT);'''
          #FOREIGN KEY (card_id) REFERENCES decks (card_id)); '''
    cursor.execute(create_cards_table_query)
    connection.commit()
    print("Table cards created successfully in PostgreSQL ")


    create_questions_table_query = '''CREATE TABLE IF NOT EXISTS questions
          (qns_id INT PRIMARY KEY,
          card_id INT,
          qns_info  TEXT)'''
          #FOREIGN KEY (card_id) REFERENCES cards (card_id)); '''
    cursor.execute(create_questions_table_query)
    connection.commit()
    print("Table questions created successfully in PostgreSQL ")


    create_answers_table_query = '''CREATE TABLE IF NOT EXISTS answers
          (ans_id INT PRIMARY KEY,
          card_id INT,
          ans_info  TEXT);'''
          #FOREIGN KEY (card_id) REFERENCES cards (card_id)); '''
    cursor.execute(create_answers_table_query)
    connection.commit()
    print("Table answers created successfully in PostgreSQL ")


    create_checking_table_query = '''CREATE TABLE IF NOT EXISTS checking
          (user_id INT PRIMARY KEY,
          card_id INT,
          deck_id INT); '''
    cursor.execute(create_checking_table_query)
    connection.commit()
    print("Table checking created successfully in PostgreSQL ")

except (Exception, psycopg2.DatabaseError) as error :
    print ("Error while creating PostgreSQL table", error)
finally:
    #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")