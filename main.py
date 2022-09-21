from aiogram import Bot, Dispatcher, types, exceptions, middlewares, executor
from aiogram.dispatcher.filters.state import State, StatesGroup

from db import User, init_db
from basic_data import TEXTS
from config import config

from json import dumps as dumps_json
from io import BytesIO
from traceback import format_exc

from typing import Callable


bot: Bot = Bot(
    token = config.bot_token,
    parse_mode = types.ParseMode.HTML
)

dp: Dispatcher = Dispatcher(
    bot = bot
)


class MailingForm(StatesGroup):
    message = State()


async def on_startup(dp: Dispatcher) -> None:
    await init_db(
        db_uri = config.db_uri,
        db_name = config.db_name
    )


class UsersMiddleware(middlewares.BaseMiddleware):
    def __init__(self):
        super(UsersMiddleware, self).__init__()

    async def on_post_process_update(self, update: types.Update, data: list, _: dict) -> None:
        if update.message:
            if update.message.chat.type == types.ChatType.PRIVATE:
                user_id: int = update.message.from_user.id

                if not await User.find_one(
                    User.user_id == user_id
                ):
                    await User(
                        user_id = user_id
                    ).insert()

        try:
            if data[0][0]:
                return

        except IndexError:
            pass

        json_object: dict = update.to_python()

        formatted_json_string: str = dumps_json(
            obj = json_object,
            indent = 2,
            ensure_ascii = False
        )

        if update.message:
            if len(formatted_json_string) > 4096:
                document: BytesIO = BytesIO(
                    initial_bytes = bytes(
                        dumps_json(
                            obj = json_object,
                            indent = 4,
                            ensure_ascii = False
                        ),
                        "utf-8"
                    )
                )

                document.name = "result.json"

                await update.message.answer_document(
                    document = document
                )

                return

            func: Callable

            if update.message.edit_date:
                func = update.message.reply
            else:
                func = update.message.answer

            await func(
                text = "<code>{formatted_json_string}</code>".format(
                    formatted_json_string = formatted_json_string
                )
            )

        elif update.inline_query:
            await update.inline_query.answer(
                results = [
                    types.InlineQueryResultArticle(
                        id = update.inline_query.id,
                        title = TEXTS["inline_query"],
                        input_message_content=types.InputTextMessageContent(
                            "<code>{formatted_json_string}</code>".format(
                                formatted_json_string = formatted_json_string
                            )
                        )
                    )
                ],
                cache_time = config.cache_time
            )


@dp.message_handler(commands="start")
async def command_start_handler(message: types.Message) -> None:
    if message.forward_date:
        return False

    await message.answer(
        text = TEXTS["start"]
    )

    return True


@dp.errors_handler(exception=exceptions.BotBlocked)
async def errors_botblocked_handler(update: types.Update, exception: exceptions.BotBlocked) -> None:
    return True


@dp.errors_handler(exception=exceptions.TelegramAPIError)
async def errors_telegram_handler(update: types.Update, exception: exceptions.TelegramAPIError) -> None:
    for owner in config.owners:
        owner: int

        await bot.send_message(
            chat_id = owner,
            text = "#error #telegram:\n{error_description}\n\nUpdate: {update}".format(
                error_description = str(exception),
                update = update.as_json()
            )
        )

    return True


@dp.errors_handler()
async def errors_all_handler(update: types.Update, exception: Exception) -> None:
    for owner in config.owners:
        owner: int

        await bot.send_message(
            chat_id = owner,
            text = "#error:\n{error_description}\n\nUpdate: {update}".format(
                error_description = format_exc(),
                update = update.as_json()
            )
        )

    return True


dp.middleware.setup(
    middleware = UsersMiddleware()
)


if __name__ == "__main__":
    executor.start_polling(
        dispatcher = dp,
        skip_updates = False,
        on_startup = on_startup
    )
