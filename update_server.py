import requests
import re
import os
import shutil
import click
from bs4 import BeautifulSoup
import subprocess
from collections import namedtuple
import colorama
from colorama import Fore, Style
from tqdm import tqdm

colorama.init(autoreset=True)

ServerVersion = namedtuple('ServerVersion', ['version', 'revision'])

URL = 'https://nightly.mtasa.com/'

SERVER_VERSION = '1.5.6'
SERVER_EXEC_NAME = 'MTA Server64.exe'

NEW_SERVER_FILE_PATH = 'tmp/mtaserver.exe'
EXTRACT_COMMAND = '7z x -tnsis -i!server -x!*\\mods -otmp -aoa ' + NEW_SERVER_FILE_PATH

LAST_VERSION_PATTERN = re.compile(r'mtasa_x64-([\d\.]+)+-rc-(\d+)-\d+\.exe')
CURRENT_VERSION_PATTERN = re.compile(r'MTA:SA Server v([\d\.]+)+-release-(\d+)')

DOWNLOAD_BAR_FORMAT = 'Downloading: ' + Fore.GREEN + '{percentage:3.0f}% {n_fmt}/{total_fmt} ' + \
    Fore.YELLOW + '[{rate_fmt}{postfix} {remaining}]'

@click.command()
def cli():
    print()
    print('Retrieving latest version...')


    def get_page_text(url):
        r = requests.get(url)
        return r.text


    def get_current_version():
        try:
            match = CURRENT_VERSION_PATTERN.match(subprocess.run(
                [SERVER_EXEC_NAME, '-v'], capture_output=True, text=True).stdout)
            return ServerVersion(match[1], match[2])
        except (FileNotFoundError):
            print("Executable file " + SERVER_EXEC_NAME + " not found")
            return False


    def get_latest_version(soup):
        download_tag = soup.find('a', string=LAST_VERSION_PATTERN)
        match = LAST_VERSION_PATTERN.match(download_tag.text)
        return ServerVersion(match[1], match[2])


    def get_latest_version_url(soup):
        download_tag = soup.find('a', string=LAST_VERSION_PATTERN)
        return URL + download_tag['href']


    def update_server(url):
        # download server
        download_server(url)

        # unpack server
        extract_server()
        move_server()
        clean()


    def download_server(url):
        os.makedirs(os.path.dirname(NEW_SERVER_FILE_PATH), exist_ok=True)

        r = requests.get(url, stream=True)
        with open(NEW_SERVER_FILE_PATH, 'wb') as f:
            with tqdm(unit="B", unit_scale=True, unit_divisor=1024, leave=True, total=int(
                    r.headers['Content-Length']), bar_format=DOWNLOAD_BAR_FORMAT) as pbar:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
                    pbar.update(len(chunk))


    def extract_server():
        print('Extracting: ...', end='')
        result = subprocess.run(EXTRACT_COMMAND, stdout=False)
        if result.returncode == 0:
            print('\rExtracting: ' + Fore.GREEN + 'Done')
        else:
            print('\rExtracting: ' + Fore.RED + 'Error')


    def move_server():
        print('Moving: ...', end='')
        try:
            source = 'tmp/server'
            dst = '.'
            for src_dir, dirs, files in os.walk(source):
                dst_dir = src_dir.replace(source, dst, 1)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                for file_ in files:
                    src_file = os.path.join(src_dir, file_)
                    dst_file = os.path.join(dst_dir, file_)
                    if os.path.exists(dst_file):
                        os.remove(dst_file)
                    shutil.move(src_file, dst_dir)

            print('\rMoving: ' + Fore.GREEN + 'Done')
        except (OSError, FileNotFoundError):
            print('\rMoving: ' + Fore.RED + 'Error')
            raise


    def clean():
        print('Cleaning: ...', end='')
        try:
            shutil.rmtree('tmp')
            print('\rCleaning: ' + Fore.GREEN + 'Done')
        except (OSError, FileNotFoundError):
            print('\rCleaning: ' + Fore.RED + 'Error')


    soup = BeautifulSoup(get_page_text(URL), 'html.parser')

    latest_version = get_latest_version(soup)
    current_version = get_current_version()

    if latest_version and current_version:
        print('  - Latest version: ' + Fore.YELLOW + 'v{}-{}'.format(*latest_version))
        print('  - Current version: ' + Fore.YELLOW + 'v{}-{}'.format(*current_version))

        if latest_version.revision > current_version.revision:
            print(Fore.YELLOW + Style.BRIGHT + 'Needs update')
            latest_version_url = get_latest_version_url(soup)
            update_server(latest_version_url)
        elif latest_version.revision == current_version.revision:
            print(Fore.GREEN + Style.BRIGHT + 'Up to date')
        elif latest_version.revision < current_version.revision:
            print(Fore.GREEN + Style.BRIGHT + 'Up to date. ' + Fore.CYAN + 'Are you from the future?')

        print()
        os.system("pause")
