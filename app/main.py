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


src_chat = getenv("SOURCES") or None
dst_chat = getenv("DESTINATIONS") or None

if src_chat and dst_chat:
    sources = {s:d for s, d in zip(src_chat.split('/'), dst_chat.split('/')) if src_chat}
    destinations = {d:s for s, d in zip(src_chat.split('/'), dst_chat.split('/')) if dst_chat}
else:
    sources = {}
    destinations = {}

source_dialogs = {}
destination_dialogs = {}

base_url=''

client = TelegramClient('session_name', getenv("API_ID"), getenv("API_HASH"))
conn = create_connection()

######################
#     Functions      #
######################


def main():
    global sources
    global destinations
    global source_dialogs
    global destination_dialogs

    try:
        for dialog in client.iter_dialogs():
            if str(dialog.id) in sources.keys():
                source_dialogs[str(dialog.id)] = dialog
        for dialog in client.iter_dialogs():
            if str(dialog.id) in destinations.keys():
                destination_dialogs[str(dialog.id)] = dialog
            if not (sources and destinations):
                print(dialog.name, 'has ID', dialog.id)
    except Exception as e:
        print(e)

async def handle_reply_message(message, dst_dialog):
    try:
        reply_to_id = message.reply_to.reply_to_msg_id
        retrieved_ids = retrieve_message(conn, reply_to_id)
        id = retrieved_ids[0][1] if retrieved_ids else None
        if id:
            try:
                response = await client.send_message(dst_dialog, message.message, file=message.media, reply_to=id)
            except Exception:
                response = await client.send_message(dst_dialog, message.message, file=message.media)
        else:
            response = await client.send_message(dst_dialog, message.message, file=message.media)
        create_message(conn, message.id, response.id)
    except Exception as e:
        print(e)

async def handle_message(message, dst_dialog):
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

        if chat_id not in source_dialogs.keys():
            return

        print(message.message)

        if message.media:
            print(message.media)
        if message.reply_to:
            await handle_reply_message(message, destination_dialogs[sources[str(chat_id)]])
        else:
            await handle_message(message, destination_dialogs[sources[str(chat_id)]])
    except Exception as e:
        print(e)

@client.on(events.MessageEdited)
async def message_edited_handler(event):
    try:
        message = event.message
        chat_id = get_peer_id(event.peer_id)

        if chat_id not in source_dialogs.keys():
            return

        retrieved_ids = retrieve_message(conn, message.id)
        id = retrieved_ids[0][1] if retrieved_ids else None
        if id:
            print(message.message)
            await client.edit_message(destination_dialogs[sources[str(chat_id)]], id, message.message, file=message.media)
    except Exception as e:
        print(e)

# @client.on(events.MessageDeleted)
# async def message_deleted_handler(event):
#     try:
#         ids = []
#         for id in event.deleted_ids:
#             retrieved_ids = retrieve_message(conn, id)
#             retrieved_id = retrieved_ids[0][1] if retrieved_ids else None
#             if retrieved_id:
#                 ids.append(retrieved_id)
#         await client.delete_messages(dst_dialog, ids)
#     except Exception as e:
#         print(e)


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
