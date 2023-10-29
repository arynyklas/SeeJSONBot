from beanie import Document, init_beanie
from pydantic import Field
from motor.motor_asyncio import AsyncIOMotorClient
from asyncio import get_event_loop

import utils


class BaseDocument(Document):
    created_at: int = Field(default_factory=utils.get_int_timestamp)


class User(BaseDocument):
    class Settings:
        name: str = "users"

    user_id: int


async def init_db(db_uri: str, db_name: str) -> None:
    client: AsyncIOMotorClient = AsyncIOMotorClient(db_uri)
    client.get_io_loop = get_event_loop

    await init_beanie(
        database = client.get_database(db_name),
        document_models = BaseDocument.__subclasses__()
    )
