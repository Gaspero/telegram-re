import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import logging

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)


SESSION_STRING = os.environ.get('SESSION_STRING', '')
API_ID = int(os.environ.get('API_ID', '0'))
API_HASH = os.environ.get('API_HASH', '')
# must be channel id (int, positive)
MASTER = int(os.environ.get('MASTER', '0'))
# must be chat id (int, negative)
SLAVE = int(os.environ.get('SLAVE', '0'))
PORT = int(os.environ.get('PORT', '8000'))

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


@client.on(events.NewMessage)
async def my_event_handler(event):
    sender = await event.get_sender()
    print(sender)
    if sender.id == MASTER:
        await client.send_message(SLAVE, event.raw_text)

client.start()
logging.info('client started')
client.run_until_disconnected()
