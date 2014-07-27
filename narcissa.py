#!/usr/bin/env python3

import subprocess
import atexit
from schedule import Scheduler
from time import sleep
from glob import glob


META_IMPORT = '# narcissa import '
scheduler = Scheduler()


def start_scrapers():
    for scraper_path in glob('scrapers/*.py'):
        with open(scraper_path) as f:
            print(scraper_path)
            scraper_data = f.read()
            exec(scraper_data)


def start_server():
    cmd = 'waitress-serve --port=5000 server:app'
    p = subprocess.Popen(cmd.split(), cwd='server')
    return p


def main():
    start_scrapers()
    server = start_server()
    atexit.register(server.terminate)
    while True:
        scheduler.run_pending()
        sleep(1)


if __name__ == '__main__':
    main()
