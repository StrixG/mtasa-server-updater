from setuptools import setup

setup(
    name='MTA Server Updater',
    version='0.1',
    py_modules=['update_server'],
    install_requires=[
        'click',
        'requests',
        'colorama',
        'tqdm',
        'beautifulsoup4'
    ],
    entry_points='''
        [console_scripts]
        updmtaserver=update_server:cli
    ''',
)