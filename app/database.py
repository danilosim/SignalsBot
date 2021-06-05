import sqlite3
from sqlite3 import Error
import datetime

def create_connection():
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect("pythonsqlite.db")
    except Error as e:
        print(e)

    return conn

def close_connection(conn):
    try:
        if conn:
            conn.close()
    except Exception as e:
        print(e)

def create_table(conn):
    cur=None
    try:
        cur = conn.cursor()
        cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='messages' ''')

        if cur.fetchone()[0]==1:
            print('Table already exists.')
        else:
            cur.execute(
                ''' CREATE TABLE messages(
                source_id INTEGER PRIMARY KEY,
                dest_id INTEGER,
                timestamp STRING
                )
                '''
            )
            conn.commit()
            print('Table created.')
    except Exception as e:
        print(e)
    finally:
        if cur:
            cur.close()

def create_message(conn, source_id, dest_id):
    cur=None
    try:
        now = datetime.datetime.now()
        sql = ''' INSERT INTO messages(source_id,dest_id,timestamp) VALUES(?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, (source_id, dest_id, now))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        if cur:
            cur.close()

def delete_messages(conn):
    cur=None
    try:
        now = datetime.datetime.now() - datetime.timedelta(7)
        sql = ''' DELETE FROM messages WHERE timestamp < ? '''
        cur = conn.cursor()
        cur.execute(sql, (now, ))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        if cur:
            cur.close()

def retrieve_message(conn, message_id):
    rows = None
    cur=None
    try:
        sql = ''' SELECT * FROM messages WHERE source_id=? '''
        cur = conn.cursor()
        cur.execute(sql, (message_id, ))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
    finally:
        if cur:
            cur.close()
    return rows
