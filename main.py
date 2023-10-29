from aiogram import Bot, Dispatcher, types, enums, exceptions
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from db import User, init_db
from basic_data import TEXTS
from config import config

import utils

from typing import List, Callable


dispatcher: Dispatcher = Dispatcher()


logger: utils.Logger = utils.get_logger(
    name = config.logger_name,
    bot_token = config.bot_token,
    chat_ids = config.logs_chat_id,
    level = config.logger_level
)


IGNORE_TELEGRAM_ERRORS: List[str] = [
    "bot was blocked",
    "Flood control exceeded",
    "not found",
    "bot is not a member"
]


class UsersMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: types.Update, data: dict) -> None:
        if event.message:
            if event.message.chat.type == enums.ChatType.PRIVATE:
                user_id: int = event.message.from_user.id

                if not await User.find_one(
                    User.user_id == user_id
                ):
                    await User(
                        user_id = user_id
                    ).insert()

        formatted_json_string: str = event.model_dump_json(
            indent = 2,
            exclude_unset = True
        )

        try:
            try:
                if event.message:
                    if len(formatted_json_string) > 4096:
                        await event.message.answer_document(
                            document = types.BufferedInputFile(
                                file = event.model_dump_json(
                                    indent = 4,
                                    exclude_unset = True
                                ).encode("utf-8"),
                                filename = "{timestamp}.txt".format(
                                    timestamp = utils.get_int_timestamp()
                                )
                            )
                        )

                        return

                    func: Callable

                    if event.message.edit_date:
                        func = event.message.reply
                    else:
                        func = event.message.answer

                    await func(
                        text = "<code>{formatted_json_string}</code>".format(
                            formatted_json_string = formatted_json_string
                        )
                    )

                elif event.inline_query:
                    await event.inline_query.answer(
                        results = [
                            types.InlineQueryResultArticle(
                                id = event.inline_query.id,
                                title = TEXTS.inline_query,
                                input_message_content = types.InputTextMessageContent(
                                    message_text = "<code>{formatted_json_string}</code>".format(
                                        formatted_json_string = formatted_json_string
                                    )
                                )
                            )
                        ],
                        cache_time = config.cache_time
                    )

            except exceptions.TelegramAPIError as exception:
                exception_message: str = exception.message

                if "not enough rights" in exception.message:
                    await event.bot.leave_chat(
                        chat_id = event.message.chat.id
                    )

                else:
                    for substring in IGNORE_TELEGRAM_ERRORS:
                        if substring in exception_message:
                            return

                    raise

        except Exception as exception:
            logger.exception(
                msg = event.model_dump_json(
                    exclude_unset = True
                ),
                exc_info = exception
            )


@dispatcher.startup()
async def on_startup() -> None:
    await init_db(
        db_uri = config.db.uri,
        db_name = config.db.name
    )


dispatcher.update.outer_middleware(
    middleware = UsersMiddleware()
)


if __name__ == "__main__":
    dispatcher.run_polling(
        Bot(
            token = config.bot_token,
            parse_mode = enums.ParseMode.HTML
        )
    )
