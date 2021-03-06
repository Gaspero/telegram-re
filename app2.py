import base64
import os

import hypercorn.asyncio
from quart import Quart, render_template_string, request

from telethon import TelegramClient, utils, events
from telethon.sessions import MemorySession
import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)


def get_env(name, message):
    if name in os.environ:
        return os.environ[name]
    return input(message)
    # return os.environ.get(name, '')


BASE_TEMPLATE = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset='UTF-8'>
        <title>Telethon + Quart</title>
    </head>
    <body>{{ content | safe }}</body>
</html>
'''

PHONE_FORM = '''
<form action='/' method='post'>
    Phone (international format): <input name='phone' type='text' placeholder='+34600000000'>
    <input type='submit'>
</form>
'''

CODE_FORM = '''
<form action='/' method='post'>
    Telegram code: <input name='code' type='text' placeholder='70707'>
    <input type='submit'>
</form>
'''

# Session name, API ID and hash to use; loaded from environmental variables
# SESSION = os.environ.get('TG_SESSION', 'quart')
# API_ID = int(get_env('TG_API_ID', 'Enter your API ID: '))
# API_HASH = get_env('TG_API_HASH', 'Enter your API hash: ')
# MASTER = int(get_env('MASTER', ''))
# SLAVE = int(get_env('SLAVE', ''))

SESSION = os.environ.get('TG_SESSION', 'quart')
API_ID = int(os.environ.get('API_ID', '0'))
API_HASH = os.environ.get('API_HASH', '')
# must be channel id (int, positive)
MASTER = int(os.environ.get('MASTER', '0'))
# must be chat id (int, negative)
SLAVE = int(os.environ.get('SLAVE', '0'))
PORT = int(os.environ.get('PORT', '8000'))

config = hypercorn.Config()
config._bind = [f'0.0.0.0:{PORT}']
# config._log = logging.Logger

# Telethon client
client = TelegramClient(MemorySession(), API_ID, API_HASH)
# client = TelegramClient(SESSION, API_ID, API_HASH)
# client.parse_mode = 'html'  # <- Render things nicely
# phone = None
phone = os.environ.get('PHONE', '')

# Quart app
app = Quart(__name__)
app.secret_key = 'CHANGE THIS TO SOMETHING SECRET'


# Connect the client before we start serving with Quart
@app.before_serving
async def startup():
    await client.connect()
    await config.log.info(phone)
    await client.send_code_request(phone)


# After we're done serving (near shutdown), clean up the client
@app.after_serving
async def cleanup():
    await client.disconnect()


@app.route('/', methods=['GET', 'POST'])
async def root():
    # We want to update the global phone variable to remember it
    # global phone

    # Check form parameters (phone/code)
    form = await request.form
    # await client.send_code_request(phone)
    # if 'phone' in form:
    #     phone = form['phone']
    #     await client.send_code_request(phone)

    if 'code' in form:
        await client.sign_in(code=form['code'])

    # If we're logged in, show them some messages from their first dialog
    if await client.is_user_authorized():
        return await render_template_string(BASE_TEMPLATE, content='<h1>Successfully logged in</h1>')


    # Ask for the phone if we don't know it yet
    if phone is None:
        return await render_template_string(BASE_TEMPLATE, content=PHONE_FORM)

    # We have the phone, but we're not logged in, so ask for the code
    return await render_template_string(BASE_TEMPLATE, content=CODE_FORM)


@client.on(events.NewMessage)
async def my_event_handler(event):
    sender = await event.get_sender()
    print(sender)
    if sender.id == MASTER:
        await client.send_message(SLAVE, event.raw_text)
    # await print('Текст:', event.raw_text, 'sender: ', sender.id)
    # print('От:', from_id, ' Текст:', text, 'sender: ', sender)

    # await print('Sender: ', event.chat_id)


async def main():
    await hypercorn.asyncio.serve(app, config)
    client.start()
    client.run_until_disconnected()


# By default, `Quart.run` uses `asyncio.run()`, which creates a new asyncio
# event loop. If we create the `TelegramClient` before, `telethon` will
# use `asyncio.get_event_loop()`, which is the implicit loop in the main
# thread. These two loops are different, and it won't work.
#
# So, we have to manually pass the same `loop` to both applications to
# make 100% sure it works and to avoid headaches.
#
# To run Quart inside `async def`, we must use `hypercorn.asyncio.serve()`
# directly.
#
# This example creates a global client outside of Quart handlers.
# If you create the client inside the handlers (common case), you
# won't have to worry about any of this, but it's still good to be
# explicit about the event loop.
if __name__ == '__main__':
    client.loop.run_until_complete(main())
