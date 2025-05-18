# XUpdates Telegram Bot

Telegram-бот, который автоматически репостит твиты из публичных аккаунтов Twitter с использованием [Nitter](https://github.com/zedeus/nitter).

---

## Настройка
Пример `config.json`

```json
{
  "bot": {
    "token": "1234567890:abcdefghigklmnopqrstuvwxyz123456789",
    "admin_ids": [1234567890]
  },
  "update": {
    "update_cd": 30,
    "update_users": ["SpaceX", "elonmusk"],
    "chat_ids": [1234567890, -1234567890123],
    "channel_tags": ["@spacenewslive"],
    "chats_users": {
      "1234567890": ["SpaceX"]
    }
  },
  "nitter_url": "http://127.0.0.1:8080",
  "proxy_url": "http://127.0.0.1:10808"
}
```

## Описание параметров

`nitter_url` *(string)* - URL на Nitter instance

`proxy_url` *(string, optional)* - URL прокси, через который будут проходить запросы к nitter

---

### `bot` Раздел с настройками бота

`token` *(string)* - API Token telegram бота, получается через [@BotFather](https://t.me/BotFather)

`admin_ids` *(array of integers, optional)* - ID telegram аккаунтов, которые могут использовать /get (если не указать, команда будет отключена)

---

### `update` - Раздел с настройками отслеживания постов в twitter аккаунтах (если не указать, ослеживания twitter не будет)

`update_cd` *(integer)* - Интервал между обновлениями в секундах

`update_users` *(array of strings)* - Теги аккаунтов в Twitter, которые нужно отслеживать

`chat_ids` *(array of integers, optional)* - ID telegram чатов, в которые будут публиковаться обновления

`channel_tags` *(array of strings, optional)* - Теги telegram каналов, в которые будут публиковаться обновления

`chats_users` *(dict of int,str and str, optional)* - Особые правила для публикования обновлений в разные чаты или каналы, если не указать, все обновления будут поститься во все чаты и каналы


## Docker

#### Запуск

```bash
docker build -t xupdates .
cp ./xupdates.service /etc/systemd/system/xupdates.service
systemctl start xupdates
```

#### Logs

```bash
journalctl -u xupdates.service -f
```
