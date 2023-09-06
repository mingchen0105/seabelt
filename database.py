'''
統一連線資料庫。\n
* 讀取特定資料: UserDB.read(SQL語法, 目標值)\n
* 讀取所有資料: UserDB.readAll(SQL語法)\n
* 異動一筆資料: UserDB.write(SQL語法, 目標值)\n
* 異動一筆資料: UserDB.writeMany(SQL語法, 含目標值的list)\n
'''

import mysql.connector
from mysql.connector import errorcode
import configparser
from time import sleep

# 抓取config.ini設定
config = configparser.ConfigParser()
config.read('config.ini')
SQL_HOST = config.get('aws-rds', 'rds_mysql_host')
SQL_USER = config.get('aws-rds', 'rds_mysql_user')
SQL_PASSWORD = config.get('aws-rds', 'rds_mysql_password')
SQL_DATABASE = config.get('aws-rds', 'rds_mysql_database')


def connectToDatabase():
    try:
        db = mysql.connector.connect(
            host=SQL_HOST,
            user=SQL_USER,
            password=SQL_PASSWORD,
            database=SQL_DATABASE
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print('資料庫連線失敗：帳號或密碼錯誤')
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print('資料庫不存在')
    else:
        print(f'已連線: {db}')
    return db


def read(sql: str, value: tuple) -> list:
    retry_counter = 0
    retry_delay = 0.7
    while retry_counter < 3:
        try:
            db = connectToDatabase()
            mycursor = db.cursor()
            mycursor.execute(sql, value)
            result = mycursor.fetchone()
        except UnboundLocalError as err:
            print(
                f'value\t{value}\ncounter = {retry_counter}\nError msg = {err}')
            retry_counter += 1
            sleep(retry_delay)
        else:
            print(f'讀取 {mycursor.rowcount} 筆資料成功')
            db.close()
            return result


def readAll(sql: str) -> list:
    retry_counter = 0
    retry_delay = 0.7
    while retry_counter < 3:
        try:
            db = connectToDatabase()
            mycursor = db.cursor()
            mycursor.execute(sql)
            result = mycursor.fetchall()
        except UnboundLocalError as err:
            print(
                f'counter = {retry_counter}\nError msg = {err}')
            retry_counter += 1
            sleep(retry_delay)
        else:
            print(f'讀取 {mycursor.rowcount} 筆資料成功')
            db.close()
            return result


def write(sql: str, value: tuple):
    retry_counter = 0
    retry_delay = 0.7
    while retry_counter < 3:
        try:
            db = connectToDatabase()
            mycursor = db.cursor()
            mycursor.execute(sql, value)
            db.commit()
        except UnboundLocalError as err:
            print(
                f'value\t{value}\ncounter = {retry_counter}\nError msg = {err}')
            retry_counter += 1
            sleep(retry_delay)
        else:
            print(f'異動 {mycursor.rowcount} 筆資料成功')
            db.close()
            break


def writeMany(sql: str, valueList: list):
    retry_counter = 0
    retry_delay = 0.7
    while retry_counter < 3:
        try:
            db = connectToDatabase()
            mycursor = db.cursor()
            for value in valueList:
                mycursor.execute(sql, value)
            db.commit()
        except UnboundLocalError as err:
            print(
                f'value\t{value}\ncounter = {retry_counter}\nError msg = {err}')
            retry_counter += 1
            sleep(retry_delay)
        else:
            print(f'異動 {mycursor.rowcount} 筆資料成功')
            db.close()
            break
