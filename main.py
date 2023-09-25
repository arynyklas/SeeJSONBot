from aiogram import Bot, Dispatcher, types, enums
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.fsm.state import State, StatesGroup

from db import User, init_db
from basic_data import TEXTS
from config import config

import utils

from typing import Callable


dispatcher: Dispatcher = Dispatcher()


logger: utils.Logger = utils.get_logger(
    name = config.logger_name,
    bot_token = config.bot_token,
    chat_ids = config.logs_chat_ids,
    level = config.logger_level
)


class MailingForm(StatesGroup):
    message: State = State()


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
            indent = 2
        )

        if event.message:
            if len(formatted_json_string) > 4096:
                await event.message.answer_document(
                    document = types.BufferedInputFile(
                        file = event.model_dump_json(
                            indent = 4
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
                            "<code>{formatted_json_string}</code>".format(
                                formatted_json_string = formatted_json_string
                            )
                        )
                    )
                ],
                cache_time = config.cache_time
            )


@dispatcher.startup()
async def on_startup() -> None:
    await init_db(
        db_uri = config.db.uri,
        db_name = config.db.name
    )


# TODO: skip exceptions.BotBlocked
@dispatcher.error()
async def error_handler(event: types.ErrorEvent) -> None:
    logger.exception(
        msg = event.update.model_dump_json(),
        exc_info = event.exception
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
