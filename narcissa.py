#!/usr/bin/env python3

import config
from utils.safe_schedule import SafeScheduler

import subprocess
import atexit
import sys
from time import sleep
from glob import glob


scheduler = SafeScheduler()


def make_exit_graceful():
    original_hook = sys.excepthook

    def new_hook(type, value, traceback):
        if type == KeyboardInterrupt:
            sys.exit("\nBye for now!")
        else:
            original_hook(type, value, traceback)

    sys.excepthook = new_hook


def start_server():
    cmd = 'waitress-serve --port=%s server:app' % config.SERVER_PORT
    p = subprocess.Popen(cmd.split(), cwd='server')
    return p


def load_scrapers():
    for scraper_path in glob('scrapers/*.py'):
        with open(scraper_path) as f:
            print(scraper_path)
            scraper_data = f.read()
            exec(scraper_data)


def main():
    make_exit_graceful()
    server = start_server()
    atexit.register(server.terminate)
    load_scrapers()
    scheduler.run_all()
    while True:
        scheduler.run_pending()
        sleep(1)


if __name__ == '__main__':
    main()
