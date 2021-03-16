import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from bot.handlers import command_start, command_help, command_check, command_check_in, command_forget_me, \
    command_forget, command_remember, command_list, update_members
from . import settings

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=settings.LOG_LEVEL,
)
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.


def main():
    """Start the bot."""

    filter_admins = Filters.user(username=settings.TGBOT_ADMIN_USERNAMES)

    # Create the Updater and pass it your bot's token.
    updater = Updater(settings.TGBOT_APIKEY)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", command_start))
    dispatcher.add_handler(CommandHandler("help", command_help))
    dispatcher.add_handler(CommandHandler("start", command_help, filters=Filters.chat_type.private))
    dispatcher.add_handler(CommandHandler("check", command_check))
    dispatcher.add_handler(CommandHandler("check_in", command_check_in))
    dispatcher.add_handler(CommandHandler("forget_me", command_forget_me))
    dispatcher.add_handler(CommandHandler("forget", command_forget, filters=filter_admins))
    dispatcher.add_handler(CommandHandler("remember", command_remember, filters=filter_admins))
    dispatcher.add_handler(CommandHandler("list", command_list))

    # TODO: /begin @username1 @username2 command that begins tracking of users joining a chat !admin
    # TODO: /end command will end tracking of users !admin
    # TODO: /mention_all command for mentioning all users remembered !admin

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
