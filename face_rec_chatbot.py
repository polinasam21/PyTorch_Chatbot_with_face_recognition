import torch
import torch.nn as nn
from torch import optim
import torch.nn.functional as F
import random
import re
import os
import itertools
import time
import cv2
import face_recognition
import speech_recognition
import psycopg2
from tkinter import *
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import shutil
import pickle
import sys


host = "127.0.0.1"
user = "postgres"
password = "qwerty"
db_name = "face_recognition_chatbot"


#-----------------------------SQL queries----------------------------------------


def sql_query(query):
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(query)
    except Exception as _ex:
        print(_ex)
    finally:
        if connection:
            connection.close()


def sql_query_with_return_fetchone(query):
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]
    except Exception as _ex:
        print(_ex)
    finally:
        if connection:
            connection.close()


def sql_query_with_return_fetchall(query):
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as _ex:
        print(_ex)
    finally:
        if connection:
            connection.close()


def create_table_images():
    query = """CREATE TABLE if not exists IMAGES (
                    ImageId serial PRIMARY KEY,
                    FaceEncoding BYTEA NOT NULL,
                    IdentifiedPersonId integer NULL,
                    CONSTRAINT fk_image_identified_person FOREIGN KEY (IdentifiedPersonId) REFERENCES IDENTIFIED_PERSONS (IdentifiedPersonId) ON DELETE CASCADE,
                    UnidentifiedPersonId integer NULL,
                    CONSTRAINT fk_image_unidentified_person FOREIGN KEY (UnidentifiedPersonId) REFERENCES UNIDENTIFIED_PERSONS (UnidentifiedPersonId) ON DELETE CASCADE,
                    DateAndTime TIMESTAMP NOT NULL,
                    CONSTRAINT check_ids CHECK ((IdentifiedPersonId IS NOT NULL AND UnidentifiedPersonId IS NULL) or (IdentifiedPersonId IS NULL AND UnidentifiedPersonId IS NOT NULL))
                    );"""
    sql_query(query)


def create_table_identified_persons():
    query = """CREATE TABLE if not exists IDENTIFIED_PERSONS(
                    IdentifiedPersonId serial PRIMARY KEY,
                    Name varchar(50) UNIQUE NOT NULL,
                    DateAndTimeOfFirstRecognition TIMESTAMP NOT NULL,
                    DateAndTimeOfLastRecognition TIMESTAMP NOT NULL
                    );"""
    sql_query(query)


def create_table_unidentified_persons():
    query = """CREATE TABLE if not exists UNIDENTIFIED_PERSONS(
                    UnidentifiedPersonId serial PRIMARY KEY,
                    DateAndTimeOfFirstRecognition TIMESTAMP NOT NULL,
                    DateAndTimeOfLastRecognition TIMESTAMP NOT NULL
                    );"""
    sql_query(query)


def create_table_dialogues():
    query = """CREATE TABLE if not exists DIALOGUES(
                    DialogId serial PRIMARY KEY,
                    Question varchar(200) NOT NULL,
                    Answer varchar(200) NOT NULL,
                    IdentifiedPersonId integer NOT NULL,
                    CONSTRAINT fk_dialog_identified_person FOREIGN KEY (IdentifiedPersonId) REFERENCES IDENTIFIED_PERSONS (IdentifiedPersonId) ON DELETE CASCADE
                    );"""
    sql_query(query)


def drop_table_images():
    query = "DROP TABLE IMAGES;"
    sql_query(query)


def drop_table_identified_persons():
    query = "DROP TABLE IDENTIFIED_PERSONS;"
    sql_query(query)


def drop_table_unidentified_persons():
    query = "DROP TABLE UNIDENTIFIED_PERSONS;"
    sql_query(query)


def drop_table_dialogues():
    query = "DROP TABLE DIALOGUES;"
    sql_query(query)


def insert_identified_person_image_into_images(face_encoding, identified_person_id):
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO IMAGES(FaceEncoding, IdentifiedPersonId, DateAndTime) VALUES (%s, %s, NOW());""",
                (face_encoding, identified_person_id)
            )
    except Exception as _ex:
        print(_ex)
    finally:
        if connection:
            connection.close()


def insert_unidentified_person_image_into_images(face_encoding, unidentified_person_id):
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO IMAGES(FaceEncoding, UnidentifiedPersonId, DateAndTime) VALUES (%s, %s, NOW());""",
                (face_encoding, unidentified_person_id))
    except Exception as _ex:
        print(_ex)
    finally:
        if connection:
            connection.close()


def insert_into_identified_persons(name):
    query = "INSERT INTO IDENTIFIED_PERSONS(Name, DateAndTimeOfFirstRecognition, DateAndTimeOfLastRecognition) VALUES ('" + name + "', NOW(), NOW());"
    sql_query(query)


def insert_into_dialogues(identified_person_id, question, answer):
    query = "INSERT INTO DIALOGUES(IdentifiedPersonId, Question, Answer) VALUES (" + str(identified_person_id) + ", '" + question + "', '" + answer + "');"
    sql_query(query)


def insert_into_identified_persons_with_date_and_time_of_first_and_last_recognitions(name,
                                                                                     date_and_time_of_first_recognition,
                                                                                     date_and_time_of_last_recognition):
    query = "INSERT INTO IDENTIFIED_PERSONS(Name, DateAndTimeOfFirstRecognition, DateAndTimeOfLastRecognition) VALUES ('" + name + "', '" + str(date_and_time_of_first_recognition) + "', '" + str(date_and_time_of_last_recognition) + "');"
    sql_query(query)


def insert_into_unidentified_persons():
    query = "INSERT INTO UNIDENTIFIED_PERSONS(DateAndTimeOfFirstRecognition, DateAndTimeOfLastRecognition) VALUES (NOW(), NOW());"
    sql_query(query)


def count_images():
    query = "SELECT COUNT(*) FROM IMAGES;"
    res = sql_query_with_return_fetchone(query)
    return res


def count_identified_persons():
    query = "SELECT COUNT(*) FROM IDENTIFIED_PERSONS;"
    res = sql_query_with_return_fetchone(query)
    return res


def count_types_of_changes():
    query = "SELECT COUNT(*) FROM TYPES_OF_CHANGES;"
    res = sql_query_with_return_fetchone(query)
    return res


def count_unidentified_persons():
    query = "SELECT COUNT(*) FROM UNIDENTIFIED_PERSONS;"
    res = sql_query_with_return_fetchone(query)
    return res


def count_images_of_identified_person(identified_person_id):
    query = "SELECT COUNT(*) FROM IMAGES WHERE IdentifiedPersonId = " + str(identified_person_id) + ";"
    res = sql_query_with_return_fetchone(query)
    return res


def count_images_of_unidentified_person(unidentified_person_id):
    query = "SELECT COUNT(*) FROM IMAGES WHERE UnidentifiedPersonId = " + str(unidentified_person_id) + ";"
    res = sql_query_with_return_fetchone(query)
    return res


def get_id_by_name_in_table_identified_persons(name):
    query = "SELECT IdentifiedPersonId FROM IDENTIFIED_PERSONS WHERE Name = '" + name + "';"
    res = sql_query_with_return_fetchone(query)
    return res


def get_name_by_id_in_table_identified_persons(identified_person_id):
    query = "SELECT Name FROM IDENTIFIED_PERSONS WHERE IdentifiedPersonId = " + str(identified_person_id) + ";"
    res = sql_query_with_return_fetchone(query)
    return res


def find_identified_person_face_encoding_in_table_images(identified_person_id):
    query = "SELECT FaceEncoding FROM IMAGES WHERE IdentifiedPersonId = " + str(identified_person_id) + ";"
    res = pickle.loads(sql_query_with_return_fetchone(query))
    return res


def find_unidentified_person_face_encoding_in_table_images(unidentified_person_id):
    query = "SELECT FaceEncoding FROM IMAGES WHERE UnidentifiedPersonId = " + str(unidentified_person_id) + ";"
    res = pickle.loads(sql_query_with_return_fetchone(query))
    return res


def is_there_this_name_in_table_identified_persons(name):
    query = "SELECT EXISTS (SELECT 1 FROM IDENTIFIED_PERSONS WHERE Name = '" + name + "');"
    res = sql_query_with_return_fetchone(query)
    return res


def is_there_this_id_in_table_unidentified_persons(unidentified_person_id):
    query = "SELECT EXISTS (SELECT 1 FROM UNIDENTIFIED_PERSONS WHERE UnidentifiedPersonId = " + str(unidentified_person_id) + ");"
    res = sql_query_with_return_fetchone(query)
    return res


def delete_from_table_unidentified_persons_by_id(unidentified_person_id):
    query = "DELETE FROM UNIDENTIFIED_PERSONS WHERE UnidentifiedPersonId = " + str(unidentified_person_id) + ";"
    sql_query(query)


def delete_from_table_dialogues_by_id(identified_person_id):
    query = "DELETE FROM DIALOGUES WHERE IdentifiedPersonId = " + str(identified_person_id) + ";"
    sql_query(query)


def get_date_and_time_of_first_recognition_in_table_unidentified_persons(unidentified_person_id):
    query = "SELECT DateAndTimeOfFirstRecognition FROM UNIDENTIFIED_PERSONS WHERE UnidentifiedPersonId = " + str(unidentified_person_id) + ";"
    res = sql_query_with_return_fetchone(query)
    return res


def get_date_and_time_of_last_recognition_in_table_unidentified_persons(unidentified_person_id):
    query = "SELECT DateAndTimeOfLastRecognition FROM UNIDENTIFIED_PERSONS WHERE UnidentifiedPersonId = " + str(unidentified_person_id) + ";"
    res = sql_query_with_return_fetchone(query)
    return res


def get_date_and_time_of_first_recognition_in_table_identified_persons(identified_person_id):
    query = "SELECT DateAndTimeOfFirstRecognition FROM IDENTIFIED_PERSONS WHERE IdentifiedPersonId = " + str(identified_person_id) + ";"
    res = sql_query_with_return_fetchone(query)
    return res


def get_date_and_time_of_last_recognition_in_table_identified_persons(identified_person_id):
    query = "SELECT DateAndTimeOfLastRecognition FROM IDENTIFIED_PERSONS WHERE IdentifiedPersonId = " + str(identified_person_id) + ";"
    res = sql_query_with_return_fetchone(query)
    return res


def update_unidentified_person_id_to_identified_person_id_in_table_images(unidentified_person_id, identified_person_id):
    query = "UPDATE IMAGES SET IdentifiedPersonId = " + str(identified_person_id) + ", UnidentifiedPersonId = NULL WHERE UnidentifiedPersonId = " + str(unidentified_person_id) + ";"
    sql_query(query)


def update_name_in_identified_persons(old_name, new_name):
    query = "UPDATE IDENTIFIED_PERSONS SET Name = '" + new_name + "' WHERE Name = '" + old_name + "';"
    sql_query(query)


def update_date_and_time_of_last_recognition_in_table_identified_persons(identified_person_id):
    query = "UPDATE IDENTIFIED_PERSONS SET DateAndTimeOfLastRecognition = NOW() WHERE IdentifiedPersonId = " + str(identified_person_id) + ";"
    sql_query(query)


def update_date_and_time_of_last_recognition_in_table_unidentified_persons(unidentified_person_id):
    query = "UPDATE UNIDENTIFIED_PERSONS SET DateAndTimeOfLastRecognition = NOW() WHERE UnidentifiedPersonId = " + str(unidentified_person_id) + ";"
    sql_query(query)


def get_ids_from_table_identified_persons():
    query = "SELECT IdentifiedPersonId FROM IDENTIFIED_PERSONS;"
    res = sql_query_with_return_fetchall(query)
    return res


def get_ids_from_table_unidentified_persons():
    query = "SELECT UnidentifiedPersonId FROM UNIDENTIFIED_PERSONS;"
    res = sql_query_with_return_fetchall(query)
    return res


def get_questions_and_answers_by_identified_person_id_in_table_dialogues(identified_person_id):
    query = "SELECT dialogues.question, dialogues.answer FROM DIALOGUES WHERE IdentifiedPersonId = " + str(identified_person_id) + ";"
    res = sql_query_with_return_fetchall(query)
    return res


#--------------------------Speech recognition------------------------------------


def listen():
    try:
        with speech_recognition.Microphone() as mic:
            sr.adjust_for_ambient_noise(source=mic, duration=0.5)
            audio = sr.listen(source=mic)
            query = sr.recognize_google(audio_data=audio, language='ru-RU').lower()
        return query
    except speech_recognition.UnknownValueError:
        return None


#----------------------------Delete dataset--------------------------------------


def delete_dataset():
    folders = os.listdir("dataset")
    for folder in folders:
        shutil.rmtree("dataset/" + folder)

    drop_table_images()
    drop_table_dialogues()
    drop_table_identified_persons()
    drop_table_unidentified_persons()

    create_table_identified_persons()
    create_table_unidentified_persons()
    create_table_images()
    create_table_dialogues()


#------------------------Changing names-----------------------------------------


def is_name_belongs_to_unidentified_person(name):
    return name[:6] == "person" and name[6:].isdigit() and is_there_this_id_in_table_unidentified_persons(int(name[6:]))


def is_name_belongs_to_identified_person(name):
    return is_there_this_name_in_table_identified_persons(name)


def change_name(old_name, new_name):
    if is_name_belongs_to_identified_person(old_name) and not (is_name_belongs_to_identified_person(new_name)) and not (
    is_name_belongs_to_unidentified_person(new_name)) and new_name != "":
        update_name_in_identified_persons(old_name, new_name)
        dialog_label1.config(text="Имя " + old_name + " изменено на " + new_name, width="50")
        dialog_label1.update_idletasks()
        if os.path.isdir("dataset/" + old_name):
            os.rename("dataset/" + old_name, "dataset/" + new_name)
    elif is_name_belongs_to_unidentified_person(old_name) and not (
    is_name_belongs_to_identified_person(new_name)) and not (
    is_name_belongs_to_unidentified_person(new_name)) and new_name != "":
        unidentified_person_id = int(old_name[6:])
        date_and_time_of_first_recognition = get_date_and_time_of_first_recognition_in_table_unidentified_persons(
            unidentified_person_id)
        date_and_time_of_last_recognition = get_date_and_time_of_last_recognition_in_table_unidentified_persons(
            unidentified_person_id)
        insert_into_identified_persons_with_date_and_time_of_first_and_last_recognitions(new_name,
                                                                                         date_and_time_of_first_recognition,
                                                                                         date_and_time_of_last_recognition)
        identified_person_id = count_identified_persons()
        update_unidentified_person_id_to_identified_person_id_in_table_images(unidentified_person_id,
                                                                              identified_person_id)
        delete_from_table_unidentified_persons_by_id(unidentified_person_id)
        dialog_label1.config(text="Имя " + old_name + " изменено на " + new_name, width="50")
        dialog_label1.update_idletasks()
        if os.path.isdir("dataset/" + old_name):
            os.rename("dataset/" + old_name, "dataset/" + new_name)
    else:
        dialog_label1.config(text="Имена введены некорректно", width="50")
        dialog_label1.update_idletasks()


def change_name_from_speech_recognition():
    global name_now, number_of_persons_in_front_of_the_camera
    if number_of_persons_in_front_of_the_camera == 0:
        dialog_label1.config(text='Перед камерой никого нет', width="50")
        dialog_label1.update_idletasks()
        return
    if number_of_persons_in_front_of_the_camera > 1:
        dialog_label1.config(text='Перед камерой находится более одного человека', width="50")
        dialog_label1.update_idletasks()
        return
    dialog_label1.config(text='Скажите имя', width="50")
    dialog_label1.update_idletasks()
    query = listen()
    if query:
        change_name(name_now, query[0].upper() + query[1:])
    else:
        dialog_label1.config(text='Не получилось распознать имя', width="50")
        dialog_label1.update_idletasks()


def change_name_from_input_person_name_in_front_of_camera():
    global input_person_name_in_front_of_camera, dialog_label1, number_of_persons_in_front_of_the_camera
    if number_of_persons_in_front_of_the_camera == 0:
        dialog_label1.config(text='Перед камерой никого нет', width="50")
        dialog_label1.update_idletasks()
        return
    if number_of_persons_in_front_of_the_camera > 1:
        dialog_label1.config(text='Перед камерой находится более одного человека', width="50")
        dialog_label1.update_idletasks()
        return
    old_name = name_now
    new_name = input_person_name_in_front_of_camera.get()
    change_name(old_name, new_name)


def change_name_from_input_now_name_and_input_new_name():
    global input_now_name, input_new_name
    old_name = input_now_name.get()
    new_name = input_new_name.get()
    change_name(old_name, new_name)


def get_identified_person_names():
    idenfified_person_ids = get_ids_from_table_identified_persons()
    identified_person_names = []
    for i in range(len(idenfified_person_ids)):
        idenfified_person_id = idenfified_person_ids[i][0]
        identified_person_names.append(get_name_by_id_in_table_identified_persons(idenfified_person_id))
    return identified_person_names


#-------------------------Output dialog------------------------------------------


def fill_dialog(name):
    global interface2_scroll
    delete_dialog_in_scroll_text()
    identified_person_id = get_id_by_name_in_table_identified_persons(name)
    identified_person_id_dialogues = get_questions_and_answers_by_identified_person_id_in_table_dialogues(identified_person_id)
    for i in range(len(identified_person_id_dialogues)):
        question = identified_person_id_dialogues[i][0]
        answer = identified_person_id_dialogues[i][1]
        interface2_scroll.insert("end", name + ": " + question + "\n")
        interface2_scroll.insert("end", "Бот: " + answer + "\n")
    interface2_scroll.see("end")


def delete_dialog_in_scroll_text():
    global interface2_scroll
    interface2_scroll.delete('1.0', 'end')


def delete_dialog():
    global names_persons_in_front_of_the_camera_now
    if len(names_persons_in_front_of_the_camera_now) == 1:
        identified_person_id = get_id_by_name_in_table_identified_persons(names_persons_in_front_of_the_camera_now[0])
        delete_from_table_dialogues_by_id(identified_person_id)
        delete_dialog_in_scroll_text()


#-----------------------------Face recognition-----------------------------------


def face_rec():
    global last_time, new_time, name_now, number_of_persons_in_front_of_the_camera, names_persons_in_front_of_the_camera_now, names_persons_in_front_of_the_camera_last, interface2_label
    success, image = cap.read()
    locations = face_recognition.face_locations(image)
    encodings = face_recognition.face_encodings(image, locations)
    is_3_sec_passed = False
    number_of_persons_in_front_of_the_camera = len(locations)
    names_persons_in_front_of_the_camera_now = []
    for face_location, face_encoding in zip(locations, encodings):
        name = ""
        recognized_identified_person_id = 0
        recognized_unidentified_person_id = 0
        identified_person_ids = get_ids_from_table_identified_persons()
        unidentified_person_ids = get_ids_from_table_unidentified_persons()
        if identified_person_ids:
            identified_person_number = len(identified_person_ids)
        else:
            identified_person_number = 0
        if unidentified_person_ids:
            unidentified_person_number = len(unidentified_person_ids)
        else:
            unidentified_person_number = 0
        for i in range(identified_person_number):
            identified_person_id = identified_person_ids[i][0]
            identified_person_face_encoding = find_identified_person_face_encoding_in_table_images(identified_person_id)
            if face_recognition.compare_faces([face_encoding], identified_person_face_encoding)[0]:
                recognized_identified_person_id = identified_person_id
                name = get_name_by_id_in_table_identified_persons(identified_person_id)
                break
        for i in range(unidentified_person_number):
            unidentified_person_id = unidentified_person_ids[i][0]
            unidentified_person_face_encoding = find_unidentified_person_face_encoding_in_table_images(
                unidentified_person_id)
            if face_recognition.compare_faces([face_encoding], unidentified_person_face_encoding)[0]:
                recognized_unidentified_person_id = unidentified_person_id
                name = "person" + str(recognized_unidentified_person_id)
                break
        top, right, bottom, left = face_location
        left_top = (left, top)
        right_bottom = (right, bottom)
        color = [255, 0, 0]
        cv2.rectangle(image, left_top, right_bottom, color, 4)
        new_time = time.time()
        if new_time - last_time >= 3:
            is_3_sec_passed = True
            face_img = image[top:bottom, left:right]
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(face_img)
            if recognized_identified_person_id != 0:
                count = count_images_of_identified_person(recognized_identified_person_id) + 1
                pil_img.save("dataset/" + name + "/" f"img_{count}.jpg")
                insert_identified_person_image_into_images(pickle.dumps(face_encoding), recognized_identified_person_id)
                update_date_and_time_of_last_recognition_in_table_identified_persons(recognized_identified_person_id)
            elif recognized_unidentified_person_id != 0:
                count = count_images_of_unidentified_person(recognized_unidentified_person_id) + 1
                pil_img.save("dataset/" + name + "/" f"img_{count}.jpg")
                insert_unidentified_person_image_into_images(pickle.dumps(face_encoding),
                                                             recognized_unidentified_person_id)
                update_date_and_time_of_last_recognition_in_table_unidentified_persons(
                    recognized_unidentified_person_id)
            else:
                count = identified_person_number + unidentified_person_number + 1
                name = f"person{count}"
                os.makedirs("dataset/" + name)
                pil_img.save("dataset/" + name + "/" + f"img_1.jpg")
                insert_into_unidentified_persons()
                insert_unidentified_person_image_into_images(pickle.dumps(face_encoding), count)
        left_bottom = (left, bottom)
        right_bottom = (right, bottom + 20)
        name_now = name
        names_persons_in_front_of_the_camera_now.append(name)
        cv2.rectangle(image, left_bottom, right_bottom, color, cv2.FILLED)
        cv2.putText(image, name, (left + 10, bottom + 15), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 4)
    if is_3_sec_passed:
        last_time = new_time

    identified_person_names = get_identified_person_names()

    if len(names_persons_in_front_of_the_camera_now) == 0 and len(names_persons_in_front_of_the_camera_last) != 0:
        interface2_label.config(text="Перед камерой никого нет")
        delete_dialog_in_scroll_text()
    elif (len(names_persons_in_front_of_the_camera_now) == len(names_persons_in_front_of_the_camera_last) == 1 and names_persons_in_front_of_the_camera_now[0] != names_persons_in_front_of_the_camera_last[0] and names_persons_in_front_of_the_camera_now[0] in identified_person_names) or (len(names_persons_in_front_of_the_camera_last) != 1 and len(names_persons_in_front_of_the_camera_now) == 1 and names_persons_in_front_of_the_camera_now[0] in identified_person_names):
        interface2_label.config(text="")
        fill_dialog(names_persons_in_front_of_the_camera_now[0])
    elif (len(names_persons_in_front_of_the_camera_now) == len(names_persons_in_front_of_the_camera_last) == 1 and names_persons_in_front_of_the_camera_now[0] != names_persons_in_front_of_the_camera_last[0] and names_persons_in_front_of_the_camera_now[0] not in identified_person_names) or (len(names_persons_in_front_of_the_camera_last) != 1 and len(names_persons_in_front_of_the_camera_now) == 1 and names_persons_in_front_of_the_camera_now[0] not in identified_person_names):
        interface2_label.config(text="Перед камерой находится неидентифицированный человек")
        delete_dialog_in_scroll_text()
    elif len(names_persons_in_front_of_the_camera_now) > 1:
        interface2_label.config(text="Перед камерой находится более одного человека")
        delete_dialog_in_scroll_text()

    names_persons_in_front_of_the_camera_last = names_persons_in_front_of_the_camera_now[:]

    frame = image
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    main_label.imgtk = imgtk
    main_label.configure(image=imgtk)
    main_label.after(10, face_rec)


def close_program():
    sys.exit()


if not os.path.isdir("dataset"):
    os.makedirs("dataset")


create_table_identified_persons()
create_table_unidentified_persons()
create_table_images()
create_table_dialogues()

last_time = time.time()
new_time = time.time()

name_now = ""
number_of_persons_in_front_of_the_camera = 0

names_persons_in_front_of_the_camera_now = []
names_persons_in_front_of_the_camera_last = []

is_dialog_window_on = False

sr = speech_recognition.Recognizer()
sr.pause_threshold = 0.5


#------------------------------Chatbot----------------------------------------------


USE_CUDA = torch.cuda.is_available()
device = torch.device("cuda" if USE_CUDA else "cpu")


PAD_token = 0
SOS_token = 1
EOS_token = 2


class Dictionary:
    def __init__(self):
        self.word_to_index = {}
        self.word_to_count = {}
        self.index_to_word = {PAD_token: "PAD", SOS_token: "SOS", EOS_token: "EOS"}
        self.num_words = 3

    def add_sentence(self, sentence):
        for word in sentence.split(' '):
            self.add_word(word)

    def add_word(self, word):
        if word not in self.word_to_index:
            self.word_to_index[word] = self.num_words
            self.word_to_count[word] = 1
            self.index_to_word[self.num_words] = word
            self.num_words += 1
        else:
            self.word_to_count[word] += 1


MAX_LENGTH = 10


def prepare_string(s):
    s = s.lower().strip()
    s = re.sub(r"([.!?])", r" \1", s)
    s = re.sub(r"[^а-яА-Я.!?]+", r" ", s)
    s = re.sub(r"\s+", r" ", s).strip()
    return s


# pairs = []
#
# max_number_of_pairs = 1000000
#
# with open('dialogues1.txt', 'r') as file1:
#     lines1 = file1.readlines()
#
#
# count = 0
#
# for i in range(len(lines1) - 1):
#     lines1[i] = lines1[i].strip()
#     lines1[i + 1] = lines1[i + 1].strip()
#     if len(lines1[i]) > 0 and len(lines1[i + 1]) > 0 and lines1[i][0] == "-" and lines1[i + 1][0] == "-":
#         pairs.append([prepare_string(lines1[i][2:]), prepare_string(lines1[i + 1][2:])])
#         count += 1
#         if count >= max_number_of_pairs:
#             break
#
# with open('dialogues2.txt', 'r') as file2:
#     lines2 = file2.readlines()
#
# for i in range(len(lines2) - 1):
#     lines2[i] = lines2[i].strip()
#     lines2[i + 1] = lines2[i + 1].strip()
#     if len(lines2[i]) > 0 and len(lines2[i + 1]) > 0 and lines2[i][0] == "-" and lines2[i + 1][0] == "-":
#         pairs.append([prepare_string(lines2[i][2:]), prepare_string(lines2[i + 1][2:])])
#         count += 1
#         if count >= max_number_of_pairs:
#             break


def pairs_smaller_than_max_len(pairs):
    used_pairs = []
    for pair in pairs:
        if len(pair[0].split(' ')) < MAX_LENGTH and len(pair[1].split(' ')) < MAX_LENGTH:
            used_pairs.append(pair)
    return used_pairs


# pairs = pairs_smaller_than_max_len(pairs)

words_dict = Dictionary()

# for pair in pairs:
#     words_dict.add_sentence(pair[0])
#     words_dict.add_sentence(pair[1])

MIN_COUNT = 3


def trim_rare_words(words_dict, pairs, MIN_COUNT):
    used_words = []

    for k, v in words_dict.word_to_count.items():
        if v >= MIN_COUNT:
            used_words.append(k)

    words_dict.word_to_index = {}
    words_dict.word_to_count = {}
    words_dict.index_to_word = {PAD_token: "PAD", SOS_token: "SOS", EOS_token: "EOS"}
    words_dict.num_words = 3

    for word in used_words:
        words_dict.add_word(word)

    used_pairs = []
    for pair in pairs:
        input_sentence = pair[0]
        output_sentence = pair[1]
        use_input_sentence = True
        use_output_sentence = True
        for word in input_sentence.split(' '):
            if word not in used_words:
                use_input_sentence = False
                break
        for word in output_sentence.split(' '):
            if word not in used_words:
                use_output_sentence = False
                break
        if use_input_sentence and use_output_sentence:
            used_pairs.append(pair)

    return used_pairs


# pairs = trim_rare_words(words_dict, pairs, MIN_COUNT)


def indexes_from_sentence(words_dict, sentence):
    return [words_dict.word_to_index[word] for word in sentence.split(' ')] + [EOS_token]


def zero_padding(l):
    return list(itertools.zip_longest(*l, fillvalue=PAD_token))


def get_binary_matrix(l):
    m = []
    for i, seq in enumerate(l):
        m.append([])
        for token in seq:
            if token == PAD_token:
                m[i].append(0)
            else:
                m[i].append(1)
    return m


def input_var(l, words_dict):
    indexes_batch = [indexes_from_sentence(words_dict, sentence) for sentence in l]
    lengths = torch.tensor([len(indexes) for indexes in indexes_batch])
    pad_list = zero_padding(indexes_batch)
    pad_var = torch.LongTensor(pad_list)
    return pad_var, lengths


def output_var(l, words_dict):
    indexes_batch = [indexes_from_sentence(words_dict, sentence) for sentence in l]
    max_target_len = max([len(indexes) for indexes in indexes_batch])
    pad_list = zero_padding(indexes_batch)
    mask = get_binary_matrix(pad_list)
    mask = torch.BoolTensor(mask)
    pad_var = torch.LongTensor(pad_list)
    return pad_var, mask, max_target_len


def batch_to_train_data(words_dict, pair_batch):
    pair_batch.sort(key=lambda x: len(x[0].split(" ")), reverse=True)
    input_batch, output_batch = [], []
    for pair in pair_batch:
        input_batch.append(pair[0])
        output_batch.append(pair[1])
    inp, lengths = input_var(input_batch, words_dict)
    output, mask, max_target_len = output_var(output_batch, words_dict)
    return inp, lengths, output, mask, max_target_len


class EncoderRNN(nn.Module):
    def __init__(self, hidden_size, embedding, n_layers=1, dropout=0):
        super(EncoderRNN, self).__init__()
        self.n_layers = n_layers
        self.hidden_size = hidden_size
        self.embedding = embedding
        self.gru = nn.GRU(hidden_size, hidden_size, n_layers, dropout=(0 if n_layers == 1 else dropout), bidirectional=True)

    def forward(self, input_seq, input_lengths, hidden=None):
        embedded = self.embedding(input_seq)
        packed = nn.utils.rnn.pack_padded_sequence(embedded, input_lengths)
        outputs, hidden = self.gru(packed, hidden)
        outputs, _ = nn.utils.rnn.pad_packed_sequence(outputs)
        outputs = outputs[:, :, :self.hidden_size] + outputs[:, : ,self.hidden_size:]
        return outputs, hidden


class Attn(nn.Module):
    def __init__(self, hidden_size):
        super(Attn, self).__init__()
        self.hidden_size = hidden_size

    def dot_score(self, hidden, encoder_output):
        return torch.sum(hidden * encoder_output, dim=2)

    def forward(self, hidden, encoder_outputs):
        attn_energies = self.dot_score(hidden, encoder_outputs)
        attn_energies = attn_energies.t()
        return F.softmax(attn_energies, dim=1).unsqueeze(1)


class DecoderRNN(nn.Module):
    def __init__(self, embedding, hidden_size, output_size, n_layers=1, dropout=0.1):
        super(DecoderRNN, self).__init__()

        self.hidden_size = hidden_size
        self.output_size = output_size
        self.n_layers = n_layers
        self.dropout = dropout

        self.embedding = embedding
        self.embedding_dropout = nn.Dropout(dropout)
        self.gru = nn.GRU(hidden_size, hidden_size, n_layers, dropout=(0 if n_layers == 1 else dropout))
        self.concat = nn.Linear(hidden_size * 2, hidden_size)
        self.out = nn.Linear(hidden_size, output_size)

        self.attn = Attn(hidden_size)

    def forward(self, input_step, last_hidden, encoder_outputs):
        embedded = self.embedding(input_step)
        embedded = self.embedding_dropout(embedded)
        rnn_output, hidden = self.gru(embedded, last_hidden)
        attn_weights = self.attn(rnn_output, encoder_outputs)
        context = attn_weights.bmm(encoder_outputs.transpose(0, 1))
        rnn_output = rnn_output.squeeze(0)
        context = context.squeeze(1)
        concat_input = torch.cat((rnn_output, context), 1)
        concat_output = torch.tanh(self.concat(concat_input))
        output = self.out(concat_output)
        output = F.softmax(output, dim=1)
        return output, hidden


def maskNLLLoss(inp, target, mask):
    nTotal = mask.sum()
    crossEntropy = -torch.log(torch.gather(inp, 1, target.view(-1, 1)).squeeze(1))
    loss = crossEntropy.masked_select(mask).mean()
    loss = loss.to(device)
    return loss, nTotal.item()


def train(input_variable, lengths, target_variable, mask, max_target_len, encoder, decoder, embedding, encoder_optimizer, decoder_optimizer, batch_size, clip, max_length=MAX_LENGTH):

    encoder_optimizer.zero_grad()
    decoder_optimizer.zero_grad()

    input_variable = input_variable.to(device)
    target_variable = target_variable.to(device)
    mask = mask.to(device)
    lengths = lengths.to("cpu")

    loss = 0
    print_losses = []
    n_totals = 0

    encoder_outputs, encoder_hidden = encoder(input_variable, lengths)

    decoder_input = torch.LongTensor([[SOS_token for _ in range(batch_size)]])
    decoder_input = decoder_input.to(device)

    decoder_hidden = encoder_hidden[:decoder.n_layers]

    use_teacher_forcing = True if random.random() < teacher_forcing_ratio else False

    if use_teacher_forcing:
        for t in range(max_target_len):
            decoder_output, decoder_hidden = decoder(decoder_input, decoder_hidden, encoder_outputs)
            decoder_input = target_variable[t].view(1, -1)
            mask_loss, nTotal = maskNLLLoss(decoder_output, target_variable[t], mask[t])
            loss += mask_loss
            print_losses.append(mask_loss.item() * nTotal)
            n_totals += nTotal
    else:
        for t in range(max_target_len):
            decoder_output, decoder_hidden = decoder(decoder_input, decoder_hidden, encoder_outputs)
            _, topi = decoder_output.topk(1)
            decoder_input = torch.LongTensor([[topi[i][0] for i in range(batch_size)]])
            decoder_input = decoder_input.to(device)
            mask_loss, nTotal = maskNLLLoss(decoder_output, target_variable[t], mask[t])
            loss += mask_loss
            print_losses.append(mask_loss.item() * nTotal)
            n_totals += nTotal

    loss.backward()

    _ = nn.utils.clip_grad_norm_(encoder.parameters(), clip)
    _ = nn.utils.clip_grad_norm_(decoder.parameters(), clip)

    encoder_optimizer.step()
    decoder_optimizer.step()

    return sum(print_losses) / n_totals


def train_iters(model_name, words_dict, pairs, encoder, decoder, encoder_optimizer, decoder_optimizer, embedding, encoder_n_layers, decoder_n_layers, save_dir, n_iteration, batch_size, print_every, save_every, clip, corpus_name, load_filename):

    training_batches = [batch_to_train_data(words_dict, [random.choice(pairs) for _ in range(batch_size)]) for _ in range(n_iteration)]

    start_iteration = 1
    print_loss = 0
    if load_filename:
        start_iteration = checkpoint['iteration'] + 1

    for iteration in range(start_iteration, n_iteration + 1):
        training_batch = training_batches[iteration - 1]
        input_variable, lengths, target_variable, mask, max_target_len = training_batch

        loss = train(input_variable, lengths, target_variable, mask, max_target_len, encoder, decoder, embedding, encoder_optimizer, decoder_optimizer, batch_size, clip)
        print_loss += loss

        if iteration % print_every == 0:
            print_loss_avg = print_loss / print_every
            print("Итерация: {}; Среднее значение функции потерь: {:.4f}".format(iteration, print_loss_avg))
            print_loss = 0

        if (iteration % save_every == 0):
            directory = os.path.join(save_dir, model_name, corpus_name, '{}-{}_{}'.format(encoder_n_layers, decoder_n_layers, hidden_size))
            if not os.path.exists(directory):
                os.makedirs(directory)
            torch.save({
                'iteration': iteration,
                'en': encoder.state_dict(),
                'de': decoder.state_dict(),
                'en_opt': encoder_optimizer.state_dict(),
                'de_opt': decoder_optimizer.state_dict(),
                'loss': loss,
                'words_dict_dict': words_dict.__dict__,
                'embedding': embedding.state_dict()
            }, os.path.join(directory, '{}_{}.tar'.format(iteration, 'checkpoint')))


class Decoder(nn.Module):
    def __init__(self, encoder, decoder):
        super(Decoder, self).__init__()
        self.encoder = encoder
        self.decoder = decoder

    def forward(self, input_seq, input_length, max_length):
        encoder_outputs, encoder_hidden = self.encoder(input_seq, input_length)
        decoder_hidden = encoder_hidden[:decoder.n_layers]
        decoder_input = torch.ones(1, 1, device=device, dtype=torch.long) * SOS_token
        all_tokens = torch.zeros([0], device=device, dtype=torch.long)
        all_scores = torch.zeros([0], device=device)
        for _ in range(max_length):
            decoder_output, decoder_hidden = self.decoder(decoder_input, decoder_hidden, encoder_outputs)
            decoder_scores, decoder_input = torch.max(decoder_output, dim=1)
            all_tokens = torch.cat((all_tokens, decoder_input), dim=0)
            all_scores = torch.cat((all_scores, decoder_scores), dim=0)
            decoder_input = torch.unsqueeze(decoder_input, 0)
        return all_tokens, all_scores


def evaluate(encoder, decoder, searcher, words_dict, sentence, max_length=MAX_LENGTH):
    indexes_batch = [indexes_from_sentence(words_dict, sentence)]
    lengths = torch.tensor([len(indexes) for indexes in indexes_batch])
    input_batch = torch.LongTensor(indexes_batch).transpose(0, 1)
    input_batch = input_batch.to(device)
    lengths = lengths.to("cpu")
    tokens, scores = searcher(input_batch, lengths, max_length)
    decoded_words = [words_dict.index_to_word[token.item()] for token in tokens]
    return decoded_words


model_name = 'model'
hidden_size = 500
encoder_n_layers = 2
decoder_n_layers = 2
dropout = 0.1
batch_size = 64

checkpoint_iter = 100000

# load_filename = None
load_filename = os.path.join(model_name,
                            '{}-{}_{}'.format(encoder_n_layers, decoder_n_layers, hidden_size),
                            '{}_checkpoint.tar'.format(checkpoint_iter))

if load_filename:
    checkpoint = torch.load(load_filename, map_location=torch.device('cpu'))
    encoder_sd = checkpoint['en']
    decoder_sd = checkpoint['de']
    encoder_optimizer_sd = checkpoint['en_opt']
    decoder_optimizer_sd = checkpoint['de_opt']
    embedding_sd = checkpoint['embedding']
    words_dict.__dict__ = checkpoint['words_dict_dict']


embedding = nn.Embedding(words_dict.num_words, hidden_size)
if load_filename:
    embedding.load_state_dict(embedding_sd)

encoder = EncoderRNN(hidden_size, embedding, encoder_n_layers, dropout)
decoder = DecoderRNN(embedding, hidden_size, words_dict.num_words, decoder_n_layers, dropout)
if load_filename:
    encoder.load_state_dict(encoder_sd)
    decoder.load_state_dict(decoder_sd)

encoder = encoder.to(device)
decoder = decoder.to(device)


clip = 50.0
teacher_forcing_ratio = 1.0
learning_rate = 0.0001
decoder_learning_ratio = 5.0
n_iteration = 100000
print_every = 1
save_every = 10000

encoder.train()
decoder.train()

encoder_optimizer = optim.Adam(encoder.parameters(), lr=learning_rate)
decoder_optimizer = optim.Adam(decoder.parameters(), lr=learning_rate * decoder_learning_ratio)
if load_filename:
    encoder_optimizer.load_state_dict(encoder_optimizer_sd)
    decoder_optimizer.load_state_dict(decoder_optimizer_sd)

# for state in encoder_optimizer.state.values():
#     for k, v in state.items():
#         if isinstance(v, torch.Tensor):
#             state[k] = v.cuda()
#
# for state in decoder_optimizer.state.values():
#     for k, v in state.items():
#         if isinstance(v, torch.Tensor):
#             state[k] = v.cuda()

# train_iters(model_name, words_dict, pairs, encoder, decoder, encoder_optimizer, decoder_optimizer,
#            embedding, encoder_n_layers, decoder_n_layers, '', n_iteration, batch_size,
#            print_every, save_every, clip, '', load_filename)


encoder.eval()
decoder.eval()

searcher = Decoder(encoder, decoder)


#---------------------------Interface---------------------------------------------


root = tk.Tk()
root.title("Face recognition Chatbot")


main_label = tk.Label(root)
main_label.pack()


interface_btn_frame = tk.Frame(root)
interface_btn_frame.pack()
interface1_btn = tk.Button(interface_btn_frame, text="Ввод имен")
interface1_btn.pack(side="left")
interface2_btn = tk.Button(interface_btn_frame, text="Общение с чат-ботом")
interface2_btn.pack(side="left")


interface1_frame = tk.Frame(root)
dialog_label1 = tk.Label(interface1_frame, text="")
dialog_label1.pack()
input_person_name_in_front_of_camera = tk.Entry(interface1_frame)
input_person_name_in_front_of_camera.pack()
interface1_name_btn = tk.Button(interface1_frame, text="Ввести имя", command=change_name_from_input_person_name_in_front_of_camera)
interface1_name_btn.pack()
interface1_voice_btn = tk.Button(interface1_frame, text="Голосовой ввод имени", command=change_name_from_speech_recognition)
interface1_voice_btn.pack()
interface1_previous_label = tk.Label(interface1_frame, text="Текущее имя:")
interface1_previous_label.pack()
input_now_name = tk.Entry(interface1_frame)
input_now_name.pack()
interface1_new_label = tk.Label(interface1_frame, text="Новое имя:")
interface1_new_label.pack()
input_new_name = tk.Entry(interface1_frame)
input_new_name.pack()
interface1_submit_btn = tk.Button(interface1_frame, text="Ввести имя", command=change_name_from_input_now_name_and_input_new_name)
interface1_submit_btn.pack()
interface1_clear_btn = tk.Button(interface1_frame, text="Очистить базу данных", command=delete_dataset)
interface1_clear_btn.pack()


interface2_frame = tk.Frame(root)
interface2_label = tk.Label(interface2_frame, text="")
interface2_label.pack()
interface2_scroll = scrolledtext.ScrolledText(interface2_frame, height=10)
interface2_scroll.pack()
interface2_entry = tk.Entry(interface2_frame)
interface2_entry.pack()
interface2_send_btn = tk.Button(interface2_frame, text="Ввести сообщение")
interface2_send_btn.pack()
interface2_voice_btn = tk.Button(interface2_frame, text="Ввести сообщение голосом")
interface2_voice_btn.pack()
interface2_clear_btn = tk.Button(interface2_frame, text="Очистить диалог", command=delete_dialog)
interface2_clear_btn.pack()

interface1_frame.pack()

cap = cv2.VideoCapture(0)
face_rec()


def show_interface1():
    global dialog_label1, input_person_name_in_front_of_camera, input_now_name, input_new_name
    dialog_label1.config(text="")
    input_person_name_in_front_of_camera.delete(0, 'end')
    input_now_name.delete(0, 'end')
    input_new_name.delete(0, 'end')
    interface2_frame.pack_forget()
    interface1_frame.pack()


def show_interface2():
    interface1_frame.pack_forget()
    interface2_frame.pack()


def send_message():

    global names_persons_in_front_of_the_camera_now

    names_identified_persons = get_identified_person_names()

    if len(names_persons_in_front_of_the_camera_now) == 1 and names_persons_in_front_of_the_camera_now[0] in names_identified_persons:
        message = interface2_entry.get()

        interface2_entry.delete(0, "end")

        interface2_scroll.insert("end", name_now + ": " + message + "\n")

        input_sentence = message
        try:
            input_sentence = prepare_string(input_sentence)
            output_words = evaluate(encoder, decoder, searcher, words_dict, input_sentence)
            output_words[:] = [x for x in output_words if not (x == 'EOS' or x == 'PAD')]

            identified_person_id_now = get_id_by_name_in_table_identified_persons(name_now)
            insert_into_dialogues(identified_person_id_now, message, ' '.join(output_words))

            interface2_scroll.insert("end", "Бот: " + ' '.join(output_words) + "\n")

        except KeyError:
            interface2_scroll.insert("end", "Бот: Я не знаю\n")

        interface2_scroll.see("end")


def send_message_voice():
    global names_persons_in_front_of_the_camera_now

    names_identified_persons = get_identified_person_names()

    if len(names_persons_in_front_of_the_camera_now) == 1 and names_persons_in_front_of_the_camera_now[0] in names_identified_persons:
        message = listen()

        interface2_entry.delete(0, "end")

        interface2_scroll.insert("end", name_now + ": " + message + "\n")

        input_sentence = message
        try:
            input_sentence = prepare_string(input_sentence)
            output_words = evaluate(encoder, decoder, searcher, words_dict, input_sentence)
            output_words[:] = [x for x in output_words if not (x == 'EOS' or x == 'PAD')]

            identified_person_id_now = get_id_by_name_in_table_identified_persons(name_now)
            insert_into_dialogues(identified_person_id_now, message, ' '.join(output_words))

            interface2_scroll.insert("end", "Бот: " + ' '.join(output_words) + "\n")

        except KeyError:
            interface2_scroll.insert("end", "Бот: Я не знаю\n")

        interface2_scroll.see("end")


interface1_btn.config(command=show_interface1)
interface2_btn.config(command=show_interface2)
interface2_send_btn.config(command=send_message)
interface2_voice_btn.config(command=send_message_voice)

root.mainloop()

