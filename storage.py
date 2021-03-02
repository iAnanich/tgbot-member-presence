import json
import os

TGBOT_DATA_DIR = 'bot_data'


def build_chat_data_filename(chat_id: str or int) -> str:
    return os.path.join(TGBOT_DATA_DIR, f'chat-data_{chat_id}.json')


def save_chat_data(chat_id: int or str, chat_data: dict) -> None:
    filename = build_chat_data_filename(chat_id=chat_id)
    with open(filename, 'w') as fp:
        json.dump(chat_data, fp)


def restore_chat_data(chat_id: int or str) -> dict:
    filename = build_chat_data_filename(chat_id=chat_id)
    if not os.path.exists(filename):
        return {}
    with open(filename) as fp:
        return json.load(fp)
