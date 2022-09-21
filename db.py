from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field

from time import time


def _created_at() -> int:
    return int(time())


class BaseDocument(Document):
    class Settings:
        use_revision: bool = False


class User(BaseDocument):
    class Collection:
        name: str = "users"

    user_id: int
    created_at: int = Field(default_factory=_created_at)


async def init_db(db_uri: str, db_name: str) -> None:
    from asyncio import get_event_loop

    client = AsyncIOMotorClient(db_uri)
    client.get_io_loop = get_event_loop

    await init_beanie(
        database = client.get_database(db_name),
        document_models = [
            User
        ]
    )
