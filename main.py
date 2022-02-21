import hashlib
import sqlite3
from random import randint
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

chars = 'qwertyuiopasdfghjklzxcvbnm1234567890-_'
codes_length = 16
server_ip = 'http://127.0.0.1:8000/'
offline_voters_count = 150
database_name = 'database.sqlite3'

app = FastAPI()
origins = [
    # "http://localhost.tiangolo.com",
    # "https://localhost.tiangolo.com",
    "http://192.168.43.76:8080/",
    "http://192.168.56.1:8080/",
    "http://127.0.0.1:8000/",
    "http://localhost:8080/",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

candidates = {
    'Владимир Симкин': {
        'percentage': 30,
        'color': 'red',
        'imagePath': 'file://localhost/C:/Users/yaros/Downloads/png.png'
    },
    'Гуськова Алена': {
        'percentage': 20,
        'color': 'blue',
        'imagePath': 'https://androidinsider.ru/wp-content/uploads/2020/07/beaytiful_sky-750x469'
                     '.jpg',
    },
    'Кириллова Диана':
        {'percentage': 10,
         'color': 'purple',
         'imagePath': 'https://avatars.mds.yandex.net/get-kinopoisk-post-img/1345014/95e44cfe0abaddb03e43181d31a9f788/960x540'
         },
    'Шапошников Артем': {
        'percentage': 2,
        'color': 'gray',
    },
    'Галочкин Иван': {
        'percentage': 5,
        'color': 'gray',
    },
    'Филиппов Яросалв': {
        'percentage': 23,
        'color': 'gray',
    },
    'Никто': {
        'percentage': 10,
        'color': 'gray',
        'imagePath': 'https://cdn-icons-png.flaticon.com/512/61/61155.png'
    },
}


class Voter(BaseModel):
    name: str
    surname: str
    patronymic: str
    password: str


class Candidate(BaseModel):
    name: str
    surname: str
    image_path: str
    offline_votes: int


def generate_code(length: int):
    global chars
    password = ''
    for j in range(codes_length):
        password += chars[randint(0, length - 1)]
    return password


# @app.post("/registration/")
# def registration(voter: Voter):
#     con = sqlite3.connect(database_name)
#     cur = con.cursor()
#     salt = generate_code(codes_length)
#     coded_password = hashlib.pbkdf2_hmac('sha256', bytes(voter.password, 'utf8'),
#                                          bytes(salt, 'utf8'), 2)
#     cur.execute('''INSERT INTO voters VALUES (null, ?, ?, ?, ?, ?, ?)''',
#                 (voter.name, voter.surname, voter.patronymic, coded_password, salt))
#     con.close()

def check_session_id(session_id):
    if session_id:
        con = sqlite3.connect(database_name)
        cur = con.cursor()
        cur.execute('''SELECT "name" FROM voters WHERE "session-id" = ?''', (session_id,))
        req = cur.fetchone()[0]
        con.close()
        if req:
            return True
    return False


def get_session_id(voter):
    if check_user_password(voter):
        con = sqlite3.connect(database_name)
        cur = con.cursor()
        cur.execute('''SELECT "session-id" FROM voters WHERE id = ?''', (get_user_id(voter),))
        session_id = cur.fetchone()[0]
        con.close()
        return session_id
    return False


def check_user_password(voter):
    user_id = get_user_id(voter)
    if user_id:
        con = sqlite3.connect(database_name)
        cur = con.cursor()
        cur.execute('''SELECT salt, password FROM voters WHERE id = ?''', (user_id,))
        salt, right_password = cur.fetchone()
        con.close()
        if hashlib.pbkdf2_hmac('sha256', bytes(voter.password, 'utf8'),
                               bytes(salt, 'utf8'), 2) == right_password:
            return True
    return False


def is_voted(session_id):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute('''SELECT "voter-session-id" from votes where "voter-session-id" = ?''',
                (session_id,))
    result = cur.fetchone()
    con.close()
    if result:
        return True
    return False


def get_user_id(voter=None, session_id=None):
    if voter:
        con = sqlite3.connect(database_name)
        cur = con.cursor()
        cur.execute('''SELECT id FROM voters WHERE name = ? and surname = ? and patronymic = ?''',
                    (voter.name, voter.surname, voter.patronymic))
        result = cur.fetchone()
        con.close()
        if result:
            result = result[0]
        else:
            result = None
        return result
    elif session_id:
        con = sqlite3.connect(database_name)
        cur = con.cursor()
        cur.execute('''SELECT id FROM voters WHERE "session-id" = ?''',
                    (session_id,))
        result = cur.fetchone()
        con.close()
        if result:
            result = result[0]
        else:
            result = None
        return result


def get_user_id_from_session_id(session_id):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute('''SELECT id FROM voters WHERE "session-id" = ?''', (session_id,))
    req = cur.fetchone()[0]
    con.close()
    if req:
        return True
    return False


@app.get('/user-name/{session_id}')
def get_user_name(session_id: str):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute('''Select name, surname, patronymic from voters where "session-id" = ?''',
                (session_id,))
    req = cur.fetchone()
    con.close()
    if req:
        return {"name": ' '.join(req)}
    return {"name": "Имя"}


class VoteRequest(BaseModel):
    session_id: str
    candidate_id: int


@app.post('/vote/')
def vote(vote_req: VoteRequest):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    result = False
    if check_session_id(vote_req.session_id) and not is_voted(vote_req.session_id):
        result = True
        cur.execute('''INSERT INTO votes VALUES (?, ?)''',
                    (vote_req.candidate_id, get_user_id(session_id=vote_req.session_id)))
        con.commit()
    con.close()
    return result


from fastapi.responses import FileResponse


@app.get('/images/{image_name}')
def return_image(image_name: str):
    return FileResponse('images/' + image_name)


@app.get('/candidates/')
def get_candidates():
    global server_ip
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute('''select id, name, surname, "image-path", "offline-votes" from 
    candidates''')
    result = cur.fetchall()
    con.close()
    if result:
        for candidate in range(len(result)):
            con = sqlite3.connect(database_name)
            cur = con.cursor()
            cur.execute('''select "candidate-id" from votes where "candidate-id" = ?''',
                        (result[candidate][0],))
            online_votes = len(cur.fetchall())
            con.close()
            result[candidate] = {
                'candidateId': result[candidate][0],
                'name': result[candidate][1],
                'surname': result[candidate][2],
                'image': server_ip + str(result[candidate][3]),
                "offlineVotes": result[candidate][4],
                "onlineVotes": online_votes,
            }
        return result
    return []


@app.get('/votes/')
def get_votes():
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute('''select id, "offline-votes" from candidates''')
    result = {}
    offline_votes = cur.fetchall()
    for data in offline_votes:
        result[data[0]] = data[1]
    cur.execute('''select "candidate-id", "voter-id" from votes''')
    online_votes = cur.fetchall()
    for data in online_votes:
        result[data[0]] += 1
    con.close()
    return result


@app.get('/percentage/')
def get_percentage():
    votes_amount = 0
    per_candidate_votes = get_votes()
    for votes in per_candidate_votes.values():
        votes_amount += votes
    for candidate_id in per_candidate_votes.keys():
        per_candidate_votes[candidate_id] = (per_candidate_votes[candidate_id] / votes_amount) * 100
    return per_candidate_votes


@app.post("/login/")
def login(voter: Voter):
    return {'session_id': get_session_id(voter)}


def is_admin_session_id(session_id):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute('''select id from voters where "session-id" = ?''', (session_id,))
    result = cur.fetchone()
    con.close()
    if result:
        return True
    return False


class SessionId(BaseModel):
    session_id: str


@app.post('/add-empty-candidate/')
def add_empty_candidate(session_id: SessionId):
    result = False
    if is_admin_session_id(session_id.session_id):
        con = sqlite3.connect(database_name)
        cur = con.cursor()
        cur.execute('''insert into candidates values (?, ?, ?, ?, ?)''',
                    (None, None, None, None, 0))
        con.commit()
        cur.execute('''SELECT MAX(`id`) FROM candidates''')
        result = cur.fetchone()
        con.close()
    return result


class DeleteCandidateSerializer(BaseModel):
    session_id: str
    candidate_id: int


@app.post('/delete-candidate/')
def delete_candidate(delete_candidate_serializer: DeleteCandidateSerializer):
    if is_admin_session_id(delete_candidate_serializer.session_id):
        con = sqlite3.connect(database_name)
        cur = con.cursor()
        cur.execute('''delete from candidates where id = ?''',
                    (delete_candidate_serializer.candidate_id,))
        cur.execute('''delete from votes where "candidate-id" = ?''',
                    (delete_candidate_serializer.candidate_id,))
        con.commit()
        con.close()
        return True
    return False


def create_candidate(name, surname, image, offline_votes):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    file_location = f"images/{image.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(image.file.read())
    cur.execute('''insert into candidates values (?, ? , ?, ?, ? )''', (None, name, surname,
                                                                        file_location,
                                                                        offline_votes))
    con.commit()
    con.close()


def is_candidate_exist(name, surname):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute('''select id from candidates where name = ? and surname = ?''', (name, surname))
    result = cur.fetchone()
    con.close()
    if result:
        return True
    return False


def save_image(image):
    file_location = f"images/{image.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(image.file.read())
    return file_location


@app.post('/change-candidate/')
def change_candidate(session_id: str = Form(...),
                     name: str = Form(...),
                     surname: str = Form(...),
                     image: Optional[List[UploadFile]] = File(None),
                     offline_votes: int = Form(...),
                     candidate_id: int = Form(...),
                     ):
    if is_admin_session_id(session_id):
        con = sqlite3.connect(database_name)
        cur = con.cursor()
        if image:
            image_path = save_image(image[0])
            cur.execute('''UPDATE candidates SET "image-path" = ?  WHERE id = ?''',
                        (image_path, candidate_id))
        cur.execute('''UPDATE candidates SET name = ?, surname = ?,
        "offline-votes" = ? WHERE id = ?''',
                    (name, surname, offline_votes, candidate_id))
        con.commit()
        con.close()
        return True
    return False


@app.get('/get-role/{session_id}')
def get_role(session_id: str):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute('''select role from voters where "session-id" = ?''', (session_id,))
    result = cur.fetchone()
    con.close()
    if result:
        result = result[0]
    return result


if __name__ == '__main__':
    try:
        import os

        command = 'uvicorn main:app --reload'
        os.system(command)
    except Exception as error:
        print(error)
