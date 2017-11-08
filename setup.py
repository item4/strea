from setuptools import find_packages, setup

install_requires = {
    # Discord
    'discord.py == 0.16.12',
    # Async request
    'cchardet >= 2.1.1',
    'aiodns >= 1.1.1',
    # Async util
    'async-timeout >= 2.0.0',
    # Database
    'SQLAlchemy >= 1.1.15',
    'sqlalchemy-utils >= 0.32.19',
    'alembic >= 0.9.6',
    # CLI
    'Click >= 6.7',
    # Configuration
    'toml >= 0.9.3',
    # i18n
    'babel >= 2.5.1',
    # Fuzzy Search
    'fuzzywuzzy[speedup] >= 0.15.1',
    # util
    'attrdict >= 2.0.0',
}

tests_require = {
    'pytest >= 3.2.3',
    'pytest-asyncio >= 0.8.0',
    'pytest-cov >= 2.5.1',
}

extras_require = {
    'tests': tests_require,
    'lint': {
        'flake8 >= 3.5.0',
        'flake8-import-order >= 0.15',
    },
}

setup(
    name='strea',
    version='0.0.0',
    description='Discord bot for SAO MD',
    url='https://discord.gg/4CkgpJH',
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'strea=strea.cli:main',
        ],
    }
)
