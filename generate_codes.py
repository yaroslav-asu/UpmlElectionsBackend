import hashlib
import sqlite3
from random import randint

chars = 'qwertyuiopasdfghjklzxcvbnm1234567890-_'
con = sqlite3.connect('database.sqlite3')
cur = con.cursor()
chars_length = len(chars)
codes_length = 16


def generate_code(length: int):
    global chars
    password = ''
    for j in range(codes_length):
        password += chars[randint(0, length - 1)]
    return password


def create_db():
    cur.execute('''CREATE TABLE Passwords
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, name text, password text, salt int)
                   ''')


def register_voter(name, surname, patronymic, password, role=0):
    salt = generate_code(codes_length)
    coded_password = hashlib.pbkdf2_hmac('sha256', bytes(password, 'utf8'),
                                         bytes(salt, 'utf8'), 2)
    session_id = generate_code(codes_length)
    cur.execute('''INSERT INTO voters VALUES (null, ?, ?, ?, ?, ?, ?, ?)''',
                (name, surname, patronymic, coded_password, salt, session_id, role))


try:
    # people = ['admin', 'c d e', 'e f a']
    #
    # for i in range(len(people)):
    #     salt = generate_code(codes_length)
    #     password = hashlib.pbkdf2_hmac('sha256', bytes(generate_code(codes_length), 'utf8'),
    #                                    bytes(salt, 'utf8'), 2)
    #     cur.execute("INSERT INTO Passwords VALUES (null, ?, ?, ?)", (
    #         people[i],
    #         str(password),
    #         salt,
    #     ))
    register_voter('c', 'c', 'c', 'c', 2)
    con.commit()
except Exception as error:
    con.close()
    print(error)
