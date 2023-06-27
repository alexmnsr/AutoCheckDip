import asyncio
import re
import aiohttp
import vk_api
import time
import clipboard
from config import id_chat, token, file_path
from samp import *

session = vk_api.VkApi(token=token)
vk = session.get_api()
chat_bot = "-176781096"

async def read_chatlog(file_path):
    with open(file_path, 'r') as file:
        file.seek(0, 2)  # Перейти в конец файла

        while True:
            line = file.readline()
            if not line:
                await asyncio.sleep(0.1)  # Подождать 0.1 секунду перед повторным чтением файла
                continue

            #send_match = re.search(r'\[A\]\s(.*)\[[0-9]+\]:\s(.*)', line)
            #if send_match:
            #     vk_send = f"{send_match.group(1)} : {send_match.group(2)}"
            #     vk.messages.send(peer_id=239759093, message=vk_send, random_id=0)

            match = re.search(r'\[A\] Игрок (\S+)', line)
            if match and 'подозревается во взломе' in line:
                player_name = match.group(1)
                print('Ник игрока:', player_name)
                await check(player_name)


async def check(name):
    checking = "/dip " + name
    id_message = vk.messages.send(chat_id=id_chat, message=checking, random_id=0)
    await asyncio.sleep(2)
    response = await get_conversations()
    for item in response:
        if f'ExBot »  Аккаунт {name}' in item['last_message']['text']:
            text = item['last_message']['text']
            account_match = re.search(r'Аккаунт (\w+)', text)
            if account_match:
                account_nickname = account_match.group(1)
            else:
                account_nickname = None

            protect_match = re.search(r'"\/protect": (.*)', text)
            if protect_match:
                protect = protect_match.group(1)
            else:
                protect = None

            # Извлечение минимального и максимального расстояния
            distance_match = re.findall(r'(\d+) км', text)
            if distance_match:
                min_distance = int(distance_match[0])
                max_distance = int(distance_match[1])
            else:
                min_distance = None
                max_distance = None
            google_auth = await get_google(account_nickname)
            if int(min_distance) > 500 and str(protect) == "не подтверждён" and str(google_auth) == "отключен":
                send_chat(f"/kick {name}")
                await asyncio.sleep(1)
                send_chat(f"/soffban {name} -1 Подозрение во взломе")
            add_chat_message(f"Ник: {name}, мин. расст: {min_distance} км, макс. расст: {max_distance} км, /protect: {protect}, g-auth: {google_auth}", "ffffff")
            clipboard.copy(name)
    return id_message


async def get_conversations():
    async with aiohttp.ClientSession() as session:
        params = {
            "count": 10,
            "access_token": token,
            "v": "5.131",
        }
        try:
            async with session.get(
                    "https://api.vk.com/method/messages.getConversations", params=params
            ) as response:
                data = await response.json()

                if "response" not in data:
                    return []

                conversations = data["response"]["items"]
                return conversations
        except Exception as e:
            return []

async def get_google(name):
    vk.messages.send(user_id=chat_bot, message=f"/ps info {name} 7", random_id=0)
    await asyncio.sleep(2)
    response = await get_conversations()
    for item in response:
        if f'G-Auth:' in item['last_message']['text']:
            text = item['last_message']['text']
            g_auth = re.search(r'G-Auth: (.*)', text)
            if g_auth:
                google_auth = g_auth.group(1)
            else:
                google_auth = None
            return google_auth


async def main():
    await read_chatlog(file_path)


if __name__ == '__main__':
    asyncio.run(main())