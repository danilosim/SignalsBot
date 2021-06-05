from dotenv import load_dotenv, find_dotenv
from os import getenv
import asyncio
from sys import exit
from telethon import TelegramClient, events
from telethon.utils import get_peer_id
from database import (
    create_connection,
    close_connection,
    retrieve_message,
    delete_messages,
    create_message,
    create_table,
)

load_dotenv(find_dotenv())


######################
# App Configurations #
######################


src_chat = getenv("SOURCE") or None
dst_chat = getenv("DESTINATION") or None
src_dialog = None
dst_dialog = None

base_url=''

client = TelegramClient('session_name', getenv("API_ID"), getenv("API_HASH"))
conn = create_connection()

######################
#     Functions      #
######################


def main():
    src_chat = getenv("SOURCE") or None
    dst_chat = getenv("DESTINATION") or None

    try:
        for dialog in client.iter_dialogs():
            if str(dialog.id) == src_chat:
                global src_dialog
                src_dialog = dialog
            if str(dialog.id) == dst_chat:
                global dst_dialog
                dst_dialog = dialog
            if not (src_chat and dst_chat):
                print(dialog.name, 'has ID', dialog.id)
    except Exception as e:
        print(e)

    if (src_chat is None or dst_chat is None):
        print("\nPlease enter SOURCE and DESTINATION in .env file")
        exit(1)

    src_chat = int(src_chat)
    dst_chat = int(dst_chat)

async def handle_reply_message(message):
    try:
        reply_to_id = message.reply_to.reply_to_msg_id
        retrieved_ids = retrieve_message(conn, reply_to_id)
        id = retrieved_ids[0][1] if retrieved_ids else None
        if id:
            response = await client.send_message(dst_dialog, message.message, file=message.media, reply_to=id)
        else:
            response = await client.send_message(dst_dialog, message.message, file=message.media)
        create_message(conn, message.id, response.id)
    except Exception as e:
        print(e)

async def handle_message(message):
    try:
        response = await client.send_message(dst_dialog, message.message, file=message.media)
        create_message(conn, message.id, response.id)
    except Exception as e:
        print(e)

@client.on(events.NewMessage(incoming=True))
async def new_message_handler(event):
    try:
        message = event.message
        chat_id = get_peer_id(event.peer_id)

        if chat_id != src_dialog.id:
            return

        print(message.message)

        if message.media:
            print(message.media)
        if message.reply_to:
            await handle_reply_message(message)
        else:
            await handle_message(message)
    except Exception as e:
        print(e)

@client.on(events.MessageEdited)
async def message_edited_handler(event):
    try:
        message = event.message
        chat_id = get_peer_id(event.peer_id)

        if chat_id != src_dialog.id:
            return

        retrieved_ids = retrieve_message(conn, message.id)
        id = retrieved_ids[0][1] if retrieved_ids else None
        if id:
            print(message.message)
            await client.edit_message(dst_dialog, id, message.message, file=message.media)
    except Exception as e:
        print(e)

@client.on(events.MessageDeleted)
async def message_deleted_handler(event):
    try:
        ids = []
        for id in event.deleted_ids:
            retrieved_ids = retrieve_message(conn, id)
            retrieved_id = retrieved_ids[0][1] if retrieved_ids else None
            if retrieved_id:
                ids.append(retrieved_id)
        await client.delete_messages(dst_dialog, ids)
    except Exception as e:
        print(e)


######################
#      Cleaners      #
######################


async def reset_connection():
    global conn
    while True:
        await asyncio.sleep(60*60)
        print('Resetting Connection')
        if conn:
            close_connection(conn)
            conn = create_connection()

async def purge_database():
    global conn
    while True:
        await asyncio.sleep(60*60*24)
        print('Purging Database')
        delete_messages(conn)


######################
#     Execution      #
######################


create_table(conn)
client.start()
main()
loop = asyncio.get_event_loop()
loop.create_task(reset_connection())
loop.create_task(purge_database())
client.run_until_disconnected()
