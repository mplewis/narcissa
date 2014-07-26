#!/usr/bin/env python3

import narcissa_config
from scrapers.utils import list_scrapers
from server import server

import sys


SCRAPERS_DIR = 'scrapers'


def start_scrapers():
    scrapers = list_scrapers(search_dir=SCRAPERS_DIR)
    for scraper in scrapers:
        module_meta = (SCRAPERS_DIR, scraper, scraper)
        exec('from %s.%s import %s' % module_meta)
        module = sys.modules['%s.%s.%s' % module_meta]
        interval = narcissa_config.SCRAPER_INTERVALS[scraper]
        print('Running every %s seconds: %s' % (interval, module))
        module.main()


def start_server():
    print('Starting server: %s' % server)
    server.app.run()


if __name__ == '__main__':
    start_scrapers()
    start_server()
