from concurrent.futures import ThreadPoolExecutor
import asyncio
import functools
import logging
import re
import socket
import discord
import config
import datetime

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

_executor = ThreadPoolExecutor(10)


def socket_receive(sock):
    return sock.recv(8192)

async def edit_channel(channel, new_name):
    try:
        await channel.edit(name=new_name)
        print("Discord api call succesful")
    except Exception as e:
        print("Exception on channel edit")
        print(e)


async def run_commands():
    edit_task = None
    while True:
        response = await send_rcon_command("status")
        try:
            # a regex to be deleted
            players_count = re.match(".*?players : (?P<players>.*?) humans.*", response,re.DOTALL).groups()[0]

            # how to edit a channel title, to be deleted too
            print("Getting discord channel")
            channel = client.get_channel(config.DISCORD_COUNT_CHANNEL)
            if edit_task:
                if not edit_task.done():
                    print("Cancelling previous discord API task")
                    edit_task.cancel()
            print("Changing discord channel name")
            edit_task = asyncio.ensure_future(edit_channel(channel, new_name))
            print("Channel name change sent to discord api with name: " + new_name)
            print("==================================== SLEEP FOR %s seconds ====================================" % config.COUNT_UPDATE_INTERVAL)
            await asyncio.sleep(config.COUNT_UPDATE_INTERVAL)

        except Exception as e:
            print(e)


async def send_rcon_command(command):
    ct = datetime.datetime.now()
    print("\nTimestamp:-", ct)
    print("Querying RCON")
    rcon_socket = None
    try:
        rcon_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error as exception:
        print("error socket %s" % exception)
    rcon_socket.connect((config.SERVER_IP, config.SERVER_PORT))
    rcon_socket.send(b'\xff\xff\xff\xffrcon "%b" %s\n' % (config.SERVER_PASSWORD.encode(), command))
    rcon_socket.settimeout(5)
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, functools.partial(socket_receive, sock=rcon_socket))
    rcon_socket.close()
    response = res.decode("cp1252")
    print("RCON response received:")
    print(response)
    return response




class MyClient(discord.Client):
    async def on_ready(self):
        print("Daemon started")
        task = client.loop.create_task(run_commands())
        # task = client.loop.create_task(get_player_names())


client = MyClient()
client.run(config.BOT_ID)
