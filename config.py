from typing import List, Dict, Union, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import json


class BotSettings(BaseModel):
    token: str
    admin_ids: Optional[List[int]] = None

class UpdateSettings(BaseModel):
    update_cd: int
    update_users: List[str]
    chats_users: Optional[Dict[str, List[str]]] = None
    chat_ids: Optional[List[int]] = None
    channel_tags: Optional[List[str]] = None


class Settings(BaseSettings):
    bot: BotSettings
    update: Optional[UpdateSettings] = None
    nitter_url: str
    proxy_url: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


def load_config(json_path: str) -> Settings:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Settings(**data)


config = load_config('config.json')
#print(config.nitter_url)
#print(config.proxy_url)
#print(config.bot.token)
#print(config.bot.admin_ids)
#print(config.update.update_cd)
#print(config.update.update_users)
#print(config.update.chat_ids)
#print(config.update.channel_tags)
