import html
import importlib
import re
import shlex
from typing import Any, Dict

from attrdict import AttrDict

from discord import Client, Message

from sqlalchemy.orm import sessionmaker

from .box import Box, box
from .orm import Base, get_database_engine

Session = sessionmaker(autocommit=True)

SPACE_RE = re.compile('\s+')


class Bot:
    """Strea"""

    def __init__(
        self,
        config: AttrDict,
        orm_base=None,
        using_box: Box=None,
    ) -> None:
        config.DATABASE_ENGINE = get_database_engine(config)

        self.client = Client()
        self.config = config
        self.orm_base = orm_base or Base
        self.box = using_box or box

        self.event = self.client.event

        for module_name in config.HANDLERS:
            importlib.import_module(module_name)

        for module_name in config.MODELS:
            importlib.import_module(module_name)

        @self.client.event
        async def on_message(message: Message):
            async def process(call: str, args: str, name: str, handler):
                match = True
                if handler.is_command:
                    match = call == self.config.PREFIX + name

                if match:
                    func_params = handler.signature.parameters
                    kwargs = {}
                    options: Dict[str, Any] = {}
                    arguments: Dict[str, Any] = {}
                    raw = args
                    if handler.use_shlex:
                        try:
                            option_chunks = shlex.split(raw)
                        except ValueError:
                            await self.say(
                                message.channel,
                                '*Error*: Can not parse this command'
                            )
                            return False
                    else:
                        option_chunks = raw.split(' ')

                    try:
                        options, argument_chunks = handler.parse_options(
                            option_chunks)
                    except SyntaxError as e:
                        await self.say(
                            message.channel,
                            '*Error*\n{}'.format(e)
                        )
                        return False

                    try:
                        arguments, remain_chunks = handler.parse_arguments(
                            argument_chunks
                        )
                    except SyntaxError as e:
                        await self.say(
                            message.channel,
                            '*Error*\n{}'.format(e)
                        )
                        return False
                    else:
                        kwargs.update(options)
                        kwargs.update(arguments)

                        sess = Session(bind=self.config.DATABASE_ENGINE)

                        if 'bot' in func_params:
                            kwargs['bot'] = self
                        if 'message' in func_params:
                            kwargs['message'] = message
                        if 'sess' in func_params:
                            kwargs['sess'] = sess
                        if 'raw' in func_params:
                            kwargs['raw'] = raw
                        if 'remain_chunks' in func_params:
                            kwargs['remain_chunks'] = remain_chunks

                        validation = True
                        if handler.channel_validator:
                            validation = await handler.channel_validator(
                                self.client,
                                message
                            )

                        if validation:
                            try:
                                res = await handler.callback(**kwargs)
                            finally:
                                sess.close()
                        else:
                            sess.close()
                            return True

                        if not res:
                            return False
                return True
            print(message.content)
            call = ''
            args = ''
            try:
                call, args = SPACE_RE.split(message.content, 1)
            except ValueError:
                call = message.content

            for name, handler in self.box.handlers['message'].items():
                res = await process(call, args, name, handler)
                if not res:
                    break
            for alias, name in self.box.aliases.items():
                handler = self.box.handlers['message'][name]
                res = await process(call, args, alias, handler)
                if not res:
                    break

    async def say(self, *args, **kwargs):
        await self.client.send_message(*args, **kwargs)

    def run(self):
        self.client.run(self.config.TOKEN)
