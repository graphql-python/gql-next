import yaml
import json
from typing import Type, TypeVar
from dataclasses import dataclass
from dataclasses_json import dataclass_json


ConfigT = TypeVar('ConfigT', bound='ConfigT')

@dataclass_json
@dataclass(frozen=True)
class Config:
    schema: str
    documents: str

    @classmethod
    def load(cls: Type[ConfigT], filename: str) -> ConfigT:
        with open(filename, 'r') as fin:
            data = yaml.load(fin)
            datas = json.dumps(data)
            return cls.from_json(datas)
