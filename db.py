# DB connection
import psycopg2
from psycopg2 import Error

try:
    connection = psycopg2.connect(user = "ypuzvnpikuyzec",
                                  password = "b508ea454fb3ea5f4831560152799b203714bc742bb8c4b000fac6b91ef28cec",
                                  host = "ec2-35-171-31-33.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "dfhns0og19dacd")

    cursor = connection.cursor()
    
    create_users_table_query = '''CREATE TABLE IF NOT EXISTS users
          (user_id INT PRIMARY KEY); '''
    cursor.execute(create_users_table_query)
    connection.commit()
    print("Table users created successfully in PostgreSQL ")


    create_decks_table_query = '''CREATE TABLE IF NOT EXISTS decks
          (deck_id SERIAL PRIMARY KEY,
          deck_name TEXT NOT NULL,
          user_id  INT  NOT NULL);'''
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


    create_check_ans_table_query = '''CREATE TABLE IF NOT EXISTS check_ans
          (user_id INT PRIMARY KEY,
          card_id INT NOT NULL,
          deck_id INT); '''
    cursor.execute(create_check_ans_table_query)
    connection.commit()
    print("Table check_ans created successfully in PostgreSQL ")

except (Exception, psycopg2.DatabaseError) as error :
    print ("Error while creating PostgreSQL table", error)
finally:
    #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
