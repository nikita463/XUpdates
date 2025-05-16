from dataclasses import dataclass
from environs import Env
from typing import List, Optional
import time


@dataclass
class TgBot:
    token: str
    admin_ids: Optional[List[int]] = None
    chat_ids: Optional[List[int]] = None
    channel_tags: Optional[List[str]] = None


@dataclass
class Config:
    tg_bot: TgBot
    nitter_url: str
    proxy_url: Optional[str]
    update_cd: int
    update_users: Optional[List[str]]


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=env.list("ADMIN_IDS", subcast=int, default=None),
            chat_ids=env.list("CHAT_IDS", subcast=int, default=None),
            channel_tags=env.list("CHANNEL_TAGS", subcast=str, default=None)
        ),
        nitter_url=env.str("NITTER_URL"),
        proxy_url=env.str("PROXY_URL", default=None),
        update_cd=env.int("UPDATE_CD"),
        update_users=env.list("UPDATE_USERS", subcast=str, default=None)
    )


config = load_config('./.env')
#print(config.nitter_url)
#print(config.proxy_url)
#print(config.tg_bot.token)
#print(config.tg_bot.admin_ids)
#print(config.tg_bot.chat_ids)
#print(config.tg_bot.channel_tags)
#print(config.update_users)
#print(config.update_cd)
