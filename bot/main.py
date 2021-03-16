import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from . import handlers
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
    filter_groups = Filters.chat_type.supergroup | Filters.chat_type.group

    # Create the Updater and pass it your bot's token.
    updater = Updater(settings.TGBOT_APIKEY)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("help", handlers.command_help))
    dispatcher.add_handler(CommandHandler("start", handlers.command_help, filters=Filters.chat_type.private))
    dispatcher.add_handler(CommandHandler("check", handlers.command_check, filters=filter_groups))
    dispatcher.add_handler(CommandHandler("check_in", handlers.command_check_in, filters=filter_groups))
    dispatcher.add_handler(CommandHandler("forget_me", handlers.command_forget_me, filters=filter_groups))
    dispatcher.add_handler(CommandHandler("forget", handlers.command_forget, filters=filter_admins & filter_groups))
    dispatcher.add_handler(CommandHandler("remember", handlers.command_remember, filters=filter_admins & filter_groups))
    dispatcher.add_handler(CommandHandler("enable", handlers.command_enable, filters=filter_admins & filter_groups))
    dispatcher.add_handler(CommandHandler("disable", handlers.command_disable, filters=filter_admins & filter_groups))
    dispatcher.add_handler(CommandHandler("debug", handlers.command_debug, filters=filter_admins & filter_groups))
    dispatcher.add_handler(CommandHandler("start", handlers.command_start, filters=filter_admins & filter_groups))
    dispatcher.add_handler(CommandHandler("list", handlers.command_list, filters=filter_groups))

    # on noncommand i.e message
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, handlers.update_members))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
