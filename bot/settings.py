import os

import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, '.env')

env = environ.Env()
env.read_env(env_file=ENV_FILE)

LOG_LEVEL = env.str('LOG_LEVEL', default='INFO')

TGBOT_APIKEY = env.str('TGBOT_APIKEY')

TGBOT_ADMIN_USERNAMES = env.str('TGBOT_ADMIN_USERNAMES').replace('@', '').split(',')

TGBOT_MAX_MENTIONS_PER_MESSAGE = 20
""" Telegram sets limit to 50 mentions in one message, 
otherwise notifications wont be sent.
https://limits.tginfo.me/en
"""
