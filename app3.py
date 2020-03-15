import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import logging
import sys
from telethon.tl.types import MessageEntityTextUrl, MessageEntityUrl, MessageEntityMention


logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO, stream=sys.stdout)


SESSION_STRING = os.environ.get('SESSION_STRING', '')
API_ID = int(os.environ.get('API_ID', '0'))
API_HASH = os.environ.get('API_HASH', '')
# must be channel id (int, positive)
MASTER = int(os.environ.get('MASTER', '0'))
# must be chat id (int, negative)
SLAVE = int(os.environ.get('SLAVE', '0'))
PORT = int(os.environ.get('PORT', '8000'))

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

channels = {1262282428: -1001469552065, 1272721495: -1001381191322}


async def forbidden(event):
    if event.message.entities:
        for entity in event.message.entities:
            if isinstance(entity, (MessageEntityTextUrl, MessageEntityUrl, MessageEntityMention)):
                return True

@client.on(events.NewMessage)
async def my_event_handler(event):
    sender = await event.get_sender()
    # print(sender)
    if sender.id in channels.keys():
        filtered = await forbidden(event)
        if not filtered:
            await client.send_message(entity=channels[sender.id], message=event.message)
        else:
            logging.info(f'Message from {sender.title} was not sent because of filter violation')

client.start()
logging.info('client started')
client.run_until_disconnected()
