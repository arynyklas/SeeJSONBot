from logging import Logger, getLogger as _getLogger
from telegram_bot_logger import TelegramMessageHandler, formatters as logger_formatters
from time import time

from typing import Union, List


def get_logger(name: str, bot_token: str, chat_ids: Union[int, str, List[Union[int, str]]], level: str) -> Logger:
    logger: Logger = _getLogger(name)

    handler: TelegramMessageHandler = TelegramMessageHandler(
        bot_token = bot_token,
        chat_ids = chat_ids,
        format_type = logger_formatters.FormatType.DOCUMENT,
        formatter = logger_formatters.TelegramHTMLTextFormatter()
    )

    logger.addHandler(
        hdlr = handler
    )

    logger.setLevel(
        level = level
    )

    return logger


def get_int_timestamp() -> int:
    return int(time())
