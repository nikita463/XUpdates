import asyncio
import aiohttp
from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, MediaUnion
from selectolax.parser import HTMLParser, Node
from typing import List, Optional, Union
from collections import deque
import logging

from utils import *
from config import config

twitter_url = 'https://x.com'
seen_ids = deque(maxlen=1000)
logger = logging.getLogger(__name__)

class Tweet:
    def __init__(self, id: int, text: str, media: List[MediaUnion] | None):
        self.id: int = id
        self.text: str = text
        self.media: List[MediaUnion] | None = media

    @classmethod
    async def create(cls, session: aiohttp.ClientSession,
                     username: str,
                     id: int,
                     text: str,
                     images: List[str],
                     videos: List[str],
                     quote_username: Optional[str],
                     quote_id: Optional[int],
                     retweet_username: Optional[str]):
        text = text.replace('@', '')
        text += "\n<i>Source: "
        if retweet_username:
            text += f"<a href='{twitter_url}/{retweet_username}'>RT</a> "
        text += f"<a href='{twitter_url}/{username}/status/{id}'>@{username}</a>"
        if quote_username and quote_id:
            text += f", <a href='{twitter_url}/{quote_username}/status/{quote_id}'>@{quote_username}</a>"
        text += "</i>"

        media = []
        for image_url in images:
            image = await get_image_InputFile(session, image_url)
            if image:
                media.append(image)
        for video_url in videos:
            video = await get_video_InputFile(session, video_url)
            if video:
                media.append(video)
            else:
                text += f"\n<a href='{video_url}'>Video</a>"
        media = media or None

        return cls(id, text, media)

    async def send(self, bot: Bot, chat_ids: Union[int, str, List[int], List[str]]):
        media = self.media
        if isinstance(chat_ids, int):
            chat_ids = [chat_ids]
        elif isinstance(chat_ids, str):
            chat_ids = [chat_ids]
        if media:
            media[0].caption = self.text
            media[0].parse_mode = 'HTML'
            tasks = []
            for chat_id in chat_ids:
                tasks.append(bot.send_media_group(chat_id, media))
            await asyncio.gather(*tasks)
        else:
            tasks = []
            for chat_id in chat_ids:
                tasks.append(bot.send_message(chat_id, self.text, parse_mode='HTML', disable_web_page_preview=True))
            await asyncio.gather(*tasks)

async def parse_tweet(session: aiohttp.ClientSession, tweet: Node, tweet_id: int) -> Tweet | None:
    username = tweet.css_first('a.tweet-avatar')
    if username is None:
        logger.warning("parse_tweet: tweet-avatar is None")
        return None
    username = username.attributes.get('href')
    if username is None:
        logger.warning("parse_tweet: tweet-avatar href is None")
        return None
    username = username[1:]

    text = tweet.css_first('div.tweet-content.media-body')
    if text is None:
        logger.warning("parse_tweet: tweet-content is None")
        return None
    text = await format_html_element(text, twitter_url)

    images_urls: List[str] = []
    videos_urls: List[str] = []
    for image in tweet.css('a.still-image'):
        image_href = image.attributes.get('href')
        if image_href is None:
            logger.warning("parse_tweet: image href is None")
        else:
            images_urls.append(config.nitter_url + image_href)
    for video in tweet.css('source'):
        video_url = video.attributes.get('src')
        if video_url is None:
            logger.warning("parse_tweet: video source href is None")
        else:
            videos_urls.append(video_url)

    quote_link = tweet.css_first('a.quote-link')
    quote_username, quote_id = None, None
    if quote_link:
        quote_link = quote_link.attributes.get('href')
        if quote_link is None:
            logger.warning("parse_tweet: quote_link href is None")
        else:
            quote_link = quote_link.split('/')
            quote_username = quote_link[1]
            quote_id = int(quote_link[-1][:-2])

    retweet_link = tweet.css_first('a.retweet-link')
    retweet_username = None
    if retweet_link:
        retweet_link = retweet_link.attributes.get('href')
        if retweet_link is None:
            logger.warning("parse_tweet: retweet_link href is None")
        else:
            retweet_username = retweet_link[1:]

    return await Tweet.create(session, username, tweet_id, text, images_urls, videos_urls, quote_username, quote_id, retweet_username)

async def fetch_tweet(session: aiohttp.ClientSession, tweet_url: str) -> Tweet | None:
    tweet_id = await get_tweet_id(tweet_url)
    if tweet_id is None:
        return None

    async with session.get(f"{config.nitter_url}/i/status/{tweet_id}", proxy=config.proxy_url) as response:
        tweet = HTMLParser(await response.text())
    tweet = tweet.css_first('div.main-tweet')
    if tweet is None:
        logger.warning("fetch_tweet: main-tweet is None")
        return None

    tweet = await parse_tweet(session, tweet, tweet_id)
    return tweet
async def fetch_tweets(session: aiohttp.ClientSession, username: str, count: int) -> List[Tweet]:
    user_url = f"{config.nitter_url}/{username}"
    async with session.get(user_url, proxy=config.proxy_url) as response:
        html_code = await response.text()
    tweets = []
    tweets_line = HTMLParser(html_code).css('div.timeline-item')
    count = min(len(tweets_line), count)
    for tweet in tweets_line[:count]:
        tweet_link = tweet.css_first('a.tweet-link')
        if tweet_link is None:
            logger.warning("fetch_tweets: tweet link is None")
            continue

        tweet_link_href = tweet_link.attributes.get('href')
        if tweet_link_href is None:
            logger.warning("fetch_tweets: tweet link href is None")
            continue

        tweet_id = await get_tweet_id(tweet_link_href)
        if tweet_id is None:
            continue
        tweets.append(await parse_tweet(session, tweet, tweet_id))
    return tweets

async def track_tweets(session: aiohttp.ClientSession, username: str, is_start: bool) -> List[Tweet]:
    if is_start:
        count = 7
    else:
        count = 5
    tweets = await fetch_tweets(session, username, count)
    new_tweets = []
    for tweet in tweets:
        id = tweet.id
        if is_start:
            seen_ids.append(id)
        if id not in seen_ids:
            new_tweets.append(tweet)
            seen_ids.append(id)
    return new_tweets
async def track_inf(session: aiohttp.ClientSession, username: str, bot: Bot):
    if config.update is None:
        return
    is_start = True
    while True:
        new_tweets = await track_tweets(session, username, is_start)
        is_start = False
        tasks = []
        if new_tweets and config.update.chat_ids:
            tasks += [tweet.send(bot, config.update.chat_ids) for tweet in new_tweets]
        if new_tweets and config.update.channel_tags:
            tasks += [tweet.send(bot, config.update.channel_tags) for tweet in new_tweets]
        await asyncio.gather(*tasks)
        await asyncio.sleep(config.update.update_cd)
