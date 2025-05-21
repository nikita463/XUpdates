import asyncio
import aiohttp
from io import BytesIO
from aiogram.types import BufferedInputFile, InputMediaPhoto, InputMediaVideo
from selectolax.parser import Node
from typing import Tuple
import logging
import time
import json

from config import config

logger = logging.getLogger(__name__)

async def format_html_element(Node: Node, url: str) -> str:
    inner_html = ""
    current = Node.child
    while current and current.html:
        inner_html += current.html
        current = current.next
    inner_html = inner_html.replace('href="/', f'href="{url}/')
    return inner_html

async def get_response_size(response: aiohttp.ClientResponse, max_size: int | None) -> Tuple[int, bytes | None]:
    size_bytes = 0
    buffer = BytesIO()
    async for chunk in response.content.iter_chunked(1024 * 1024):
        size_bytes += len(chunk)
        buffer.write(chunk)
        if max_size and size_bytes > max_size:
            return size_bytes, None
    return size_bytes, buffer.getvalue()

async def get_video_size(videoUrl: str) -> Tuple[int, int]:
    size = videoUrl.split('/')[-2]
    size = size.split('x')
    if len(size) != 2:
        logger.warning(f"{time.time()}: get_video_size: len(size) != 2")
    return int(size[0]), int(size[1])

async def get_tweet_id(tweet_url: str) -> int | None:
    tweet_id = tweet_url.split('/')[-1]
    if tweet_id[tweet_id.find('#')] == '#':
        tweet_id = tweet_id[:tweet_id.find('#')]
    if tweet_id[tweet_id.find('?')] == '?':
        tweet_id = tweet_id[:tweet_id.find('?')]
    if not tweet_id.isdigit():
        logger.warning(f"{time.time()}: get_tweet_id: tweet_id not digit")
        return None
    return int(tweet_id)


async def get_image_InputFile(session: aiohttp.ClientSession, image_url: str) -> InputMediaPhoto | None:
    max_size = 50 * 1024 * 1024
    async with session.get(image_url, proxy=config.proxy_url) as response:
        try:
            response.raise_for_status()
        except aiohttp.ClientConnectorError:
            logger.error(f"{time.time()}: get_image_InputFile: ClientConnectorError")
            return None
        except aiohttp.ClientResponseError as e:
            logger.error(f"{time.time()}: get_image_InputFile: ClientResponse: {e.status}")
            return None
        except asyncio.TimeoutError:
            logger.error(f"{time.time()}: get_image_InputFile: TimeoutError")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"{time.time()}: get_image_InputFile: ClientError: {e}")
            return None

        content_length, image_data = await get_response_size(response, max_size)
        if content_length > max_size:
            return None
        if image_data is None:
            logger.warning(f"{time.time()}: get_image_InputFile: image_data is None, url: {image_url}")
            return None
    inputFile = BufferedInputFile(file=image_data, filename="image.jpg")
    return InputMediaPhoto(media=inputFile)

async def get_video_InputFile(session: aiohttp.ClientSession, video_url: str) -> InputMediaVideo | None:
    max_size = 50 * 1024 * 1024
    async with session.get(video_url, proxy=config.proxy_url) as response:
        try:
            response.raise_for_status()
        except aiohttp.ClientConnectorError:
            logger.error(f"{time.time()}: get_video_InputFile: ClientConnectorError")
            return None
        except aiohttp.ClientResponseError as e:
            logger.error(f"{time.time()}: get_video_InputFile: ClientResponse: {e.status}")
            return None
        except asyncio.TimeoutError:
            logger.error(f"{time.time()}: get_video_InputFile: TimeoutError")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"{time.time()}: get_video_InputFile: ClientError: {e}")
            return None

        content_length, video_data = await get_response_size(response, max_size)
        if content_length > max_size:
            return None
        if video_data is None:
            logger.warning(f"{time.time()}: get_video_InputFile: video_data is None, url: {video_url}")
            return None
    inputFile = BufferedInputFile(file=video_data, filename="video.mp4")
    width, height = await get_video_size(video_url)
    return InputMediaVideo(media=inputFile, width=width, height=height, supports_streaming=True)


async def is_admin(user_id) -> bool:
    if config.bot.admin_ids:
        return user_id in config.bot.admin_ids
    return False

async def get_sessions_health(session: aiohttp.ClientSession):
    async with session.get("http://77.239.112.57:8080/.health") as response:
        health = json.loads(await response.text())
    msg = '```\n'
    msg += f"Total sessions: {health['sessions']['total']}\nLimited sessions: {health['sessions']['limited']}\n"
    msg += f"Total requests: {health['requests']['total']}\n"
    for key in health['requests']['apis']:
        msg += f"{key}: {health['requests']['apis'][key]}\n"
    msg += '```'
    return msg
