from pathlib import Path
from sys import argv
from pydantic import BaseModel
from yaml import load as load_yaml, Loader

from typing import List, Union


CONFIG_FILEPATH: Path = Path(__file__).parent / (
    "test_config.yml"
    if "t" in argv
    else
    "config.yml"
)


class DBConfig(BaseModel):
    name: str
    uri: str


class Config(BaseModel):
    bot_token: str
    logger_name: str
    logs_chat_ids: List[Union[int, str]]
    logger_level: str
    db: DBConfig
    cache_time: int


with CONFIG_FILEPATH.open("r", encoding="utf-8") as file:
    _config_data: dict = load_yaml(
        stream = file,
        Loader = Loader
    )


config: Config = Config.parse_obj(
    obj = _config_data
)
