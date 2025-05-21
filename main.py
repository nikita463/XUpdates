import asyncio
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from tweet import track_inf, fetch_tweet
from utils import is_admin, get_tweet_id, get_sessions_health
from config import config

bot = Bot(token=config.bot.token)
dp = Dispatcher()
session: ClientSession | None = None

@dp.message(Command(commands=['id']))
async def process_id(message: Message):
    if message.from_user is None:
        return
    await message.answer(f"Chat id: `{message.chat.id}`\nUser id: `{message.from_user.id}`", parse_mode='Markdown')

@dp.message(Command(commands=['health']))
async def process_health(message: Message):
    if not (message.from_user and await is_admin(message.from_user.id)):
        return
    if session is None:
        await message.answer("ClientSession не запущен")
        return
    await message.answer(await get_sessions_health(session), parse_mode='Markdown')

@dp.message(Command(commands=['get']))
async def process_get(message: Message):
    if not (message.text and message.from_user and await is_admin(message.from_user.id)):
        return
    if len(message.text.split()) < 2:
        await message.answer("После /get напишите id поста или ссылку на него")
        return

    tweet_id = await get_tweet_id(message.text.split()[1])
    if tweet_id is None:
        await message.answer("Неверный id или ссылка")
        return

    if session is None:
        await message.answer("ClientSession не запущен")
        return
    tweet = await fetch_tweet(session, f"https://x.com/i/status/{tweet_id}")
    if tweet is None:
        await message.answer("Твит не найден")
        return

    await tweet.send(bot, message.chat.id, True)
    try:
        await message.delete()
    except:
        pass


async def main():
    global session
    session = ClientSession()

    if config.update:
        for username in config.update.update_users:
            asyncio.create_task(track_inf(session, username, bot))
    await dp.start_polling(bot)


asyncio.run(main())
