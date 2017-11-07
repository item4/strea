import importlib

from attrdict import AttrDict

from discord import Client

from sqlalchemy.orm import sessionmaker

from .orm import Base, get_database_engine

Session = sessionmaker(autocommit=True)


class Bot:
    """Strea"""

    def __init__(self, config: AttrDict, orm_base=None) -> None:
        config.DATABASE_ENGINE = get_database_engine(config)

        self.client = Client()
        self.config = config
        self.orm_base = orm_base or Base

        self.event = self.client.event

        for module_name in config.MODELS:
            importlib.import_module(module_name)

    def run(self):
        self.client.run(self.config.TOKEN)
