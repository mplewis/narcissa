#!/usr/bin/env python3

import config

import subprocess
import atexit
import schedule
from time import sleep
from glob import glob


def start_scrapers():
    for scraper in glob('scrapers/*.py'):
        with open(scraper) as f:
            exec(f.read())


def start_server():
    cmd = 'waitress-serve --port=5000 server:app'
    p = subprocess.Popen(cmd.split(), cwd='server')
    return p


def kill_process(subprocess):
    subprocess.terminate()


if __name__ == '__main__':
    start_scrapers()
    server = start_server()
    atexit.register(kill_process, server)
    while True:
        schedule.run_pending()
        sleep(1)
