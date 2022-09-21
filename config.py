from dataclasses import dataclass
from json import load as load_json, dump as dump_json

from typing import List


CONFIG_FILENAME: str = "config.json"


@dataclass
class Config:
    bot_token: str
    db_uri: str
    db_name: str
    owners: List[int]
    cache_time: int


def save_config(config: dict) -> None:
    with open(CONFIG_FILENAME, "w", encoding="utf-8") as file:
        dump_json(
            obj = config,
            fp = file,
            ensure_ascii = False,
            indent = 4
        )


with open(CONFIG_FILENAME, "r", encoding="utf-8") as file:
    config: Config = Config(
        **load_json(
            fp = file
        )
    )
