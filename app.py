import os
from telethon import TelegramClient, events


api_id = int(os.environ.get('api_id', 5000))
api_hash = int(os.environ.get('api_hash', 5000))

client = TelegramClient('anon', api_id, api_hash)


@client.on(events.NewMessage)
async def my_event_handler(event):
    if 'привет' in event.raw_text:
        await client.send_message('+79992007908', event.raw_text)

client.start()
client.run_until_disconnected()
