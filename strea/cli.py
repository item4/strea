import functools
import os.path
import pathlib
from typing import List, Optional, Type

from alembic import command
from alembic.config import Config as AlembicConfig

import click


from .bot import Bot, Session
from .config import load
from .saomd import MigrationStatus, ScoutMigration


__all__ = 'error', 'load_config', 'main', 'strea'


class Config(AlembicConfig):
    def get_template_directory(self):
        package_dir = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(package_dir, 'templates')


def error(message: str):
    """Echo and die with error message"""

    click.echo('Error: ' + message, err=True)
    raise SystemExit(1)


def load_config(func):
    """Decorator for add load config file option"""

    @functools.wraps(func)
    def internal(*args, **kwargs):
        filename = kwargs.pop('config')
        if filename is None:
            click.echo('--config option is required.', err=True)
            raise SystemExit(1)

        config = load(pathlib.Path(filename))
        kwargs['config'] = config
        return func(*args, **kwargs)

    decorator = click.option(
        '--config',
        '-c',
        type=click.Path(exists=True),
        envvar='YUI_CONFIG_FILE_PATH',
    )

    return decorator(internal)


@click.group()
def strea():
    """Strea"""


@strea.command()
@load_config
def run(config):
    """Run YUI."""

    bot = Bot(config)
    bot.run()


@strea.command()
@load_config
def init_db(config):
    """Creates a new migration repository."""

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config()
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', config.DATABASE_URL)

    c.config_file_name = os.path.join(directory, 'alembic.ini')

    command.init(c, directory, 'chatterbox')


@strea.command()
@click.option('--message', '-m')
@click.option('--autogenerate', is_flag=True, default=False)
@click.option('--sql', is_flag=True, default=False)
@click.option('--head', default='head')
@click.option('--splice', is_flag=True, default=False)
@click.option('--branch-label')
@click.option('--version-path')
@click.option('--rev-id')
@load_config
def revision(
        config,
        message: Optional[str],
        autogenerate: bool,
        sql: bool,
        head: str,
        splice: bool,
        branch_label: Optional[str],
        version_path: Optional[str],
        rev_id: Optional[str]
):
    """Create a new revision file."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.revision(
        c,
        message,
        autogenerate=autogenerate,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
        rev_id=rev_id
    )


@strea.command()
@click.option('--message', '-m')
@click.option('--sql', is_flag=True, default=False)
@click.option('--head', default='head')
@click.option('--splice', is_flag=True, default=False)
@click.option('--branch-label')
@click.option('--version-path')
@click.option('--rev-id')
@load_config
def migrate(
        config,
        message: Optional[str],
        sql: bool,
        head: str,
        splice: bool,
        branch_label: Optional[str],
        version_path: Optional[str],
        rev_id: Optional[str]
):
    """Alias for 'revision --autogenerate'"""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.revision(
        c,
        message,
        autogenerate=True,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
        rev_id=rev_id
    )


@strea.command()
@click.argument('revision', default='current')
@load_config
def edit(config, revision: str):
    """Edit current revision."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.edit(c, revision)


@strea.command()
@click.option('--rev-id')
@click.option('--branch-label')
@click.option('--message', '-m')
@click.argument('revisions', nargs=-1)
@load_config
def merge(
        config,
        revisions: str,
        message: Optional[str],
        branch_label=Optional[str],
        rev_id=Optional[str]
):
    """Merge two revisions together.  Creates a new migration file."""
    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.merge(
        c,
        revisions,
        message=message,
        branch_label=branch_label,
        rev_id=rev_id
    )


@strea.command()
@click.option('--tag')
@click.option('--sql', is_flag=True, default=False)
@click.argument('revision', default='head')
@load_config
def upgrade(config, revision: str, sql: bool, tag: Optional[str]):
    """Upgrade to a later version."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.upgrade(c, revision, sql=sql, tag=tag)


@strea.command()
@click.option('--tag')
@click.option('--sql', is_flag=True, default=False)
@click.argument('revision', default='-1')
@load_config
def downgrade(config, revision: str, sql: bool, tag: str):
    """Revert to a previous version."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.downgrade(c, revision, sql=sql, tag=tag)


@strea.command()
@click.argument('revision', default='head')
@load_config
def show(config, revision: str):
    """Show the revision denoted by the given symbol."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.show(c, revision)


@strea.command()
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.option('--rev-range', '-r')
@load_config
def history(config, verbose: bool, rev_range: Optional[str]):
    """List changeset scripts in chronological order."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.history(c, rev_range, verbose=verbose)


@strea.command()
@click.option('--resolve-dependencies', is_flag=True, default=False)
@click.option('--verbose', '-v', is_flag=True, default=False)
@load_config
def heads(config, verbose: bool, resolve_dependencies: bool):
    """Show current available heads in the script directory."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.heads(
        c,
        verbose=verbose,
        resolve_dependencies=resolve_dependencies
    )


@strea.command()
@click.option('--verbose', '-v', is_flag=True, default=False)
@load_config
def branches(config, verbose: bool):
    """Show current branch points."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.branches(c, verbose=verbose)


@strea.command()
@click.option('--verbose', '-v', is_flag=True, default=False)
@load_config
def current(config, verbose: bool):
    """Display the current revision for each database."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.current(c, verbose=verbose)


@strea.command()
@click.option('--tag')
@click.option('--sql', is_flag=True, default=False)
@click.argument('revision', default='head')
@load_config
def stamp(config, revision: str, sql: bool, tag: Optional[str]):
    """'stamp' the revision table with the given revision; don't run any
    migrations."""

    bot = Bot(config)

    directory = os.path.join('strea', 'models', 'migrations')
    c = Config(os.path.join(directory, 'alembic.ini'))
    c.set_main_option('script_location', directory)
    c.set_main_option('sqlalchemy.url', bot.config.DATABASE_URL)
    c.attributes['Base'] = bot.orm_base

    command.stamp(c, revision, sql=sql, tag=tag)


@strea.command('create-saomd-scout-data')
@load_config
def create_saomd_scout_data(config):
    """Create SAOMD scout data."""

    bot = Bot(config)

    sess = Session(bind=bot.config.DATABASE_ENGINE)
    subclasses: List[Type[ScoutMigration]] = ScoutMigration.__subclasses__()
    for cls in subclasses:
        scout = cls()
        result = scout.patch(sess)
        if result == MigrationStatus.passed:
            click.echo(f'{cls.title}는 이미 최신({cls.version})입니다.')
        elif result == MigrationStatus.create:
            click.echo(f'{cls.title}는 v{cls.version}으로 새로 만듭니다.')
        elif result == MigrationStatus.update:
            click.echo(f'{cls.title}는 구버전이라 v{cls.version}으로 올립니다.')

    click.echo('처리 완료')


main = strea
