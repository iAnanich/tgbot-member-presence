#!/usr/bin/env python
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import re
import logging
from typing import List

import environ
from telegram import Update, Bot, User
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import storage
from utils import extract_usernames_from_args

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


# Configure env
env = environ.Env()
env.read_env(file='.env')


HELP = '''
I was created to help you check out if user is in chat. 
Add me to a chat, write down nicknames (in a @nIck_Name14 format) and call me with /check command in separate message.
I will check if users listed in first message are present in chat and tell you if someone is missing.
'''


class CHAT_DATA:
    MEMBERS_BY_USERNAME = 'members_by_username'


def _remember_chat_member(user: User, context: CallbackContext):
    context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME][user.username] = {
        'id': user.id,
    }


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def command_start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(HELP)


def command_help(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(HELP)


def command_check(update: Update, context: CallbackContext) -> None:
    """Check presence of users listed in message, reply to which calls the command."""

    if not context.chat_data:
        context.chat_data.update(storage.restore_chat_data(chat_id=update.effective_chat.id))

    if update.effective_user.username not in context.chat_data['members_by_username']:
        _remember_chat_member(user=update.effective_user, context=context)

    present_usernames = set(context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME].keys())
    mentioned_usernames = set(
        # username without @ char
        un[1:]
        for un in extract_usernames_from_args(arguments=context.args)
    )
    missing_usernames = mentioned_usernames.difference(present_usernames)

    if missing_usernames:
        update.message.reply_text(
            f'Following users are missing: {" ".join("@"+un for un in missing_usernames)}'
        )
    else:
        update.message.reply_text(
            f'All mentioned users are present!',
        )


def update_members(update: Update, context: CallbackContext) -> None:
    """Remember new chat users."""

    if not context.chat_data:
        context.chat_data.update(storage.restore_chat_data(chat_id=update.effective_chat.id))

    if CHAT_DATA.MEMBERS_BY_USERNAME not in context.chat_data:
        context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME] = []

    for user in update.message.new_chat_members:
        _remember_chat_member(user=user, context=context)

    if update.message.left_chat_member:
        context.chat_data.pop(update.message.left_chat_member.username)

    storage.save_chat_data(chat_id=update.effective_chat.id, chat_data=context.chat_data)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(env.str('TGBOT_APIKEY'))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", command_start))
    dispatcher.add_handler(CommandHandler("help", command_help))
    dispatcher.add_handler(CommandHandler("check", command_check))

    # TODO: /check_in command for user to mark themselves as members of chat
    # TODO: /begin @username1 @username2 command that begins tracking of users joining a chat

    # TODO: /forget @username1 @username2 command for removing user from data of that chat
    # TODO: /mention_all command for mentioning all users remembered
    # TODO: /list command lists all remembered users

    # on noncommand i.e message
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, update_members))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
