#!/usr/bin/env python3

import config

import importlib

from scrapers.list_scrapers import list_scrapers


SCRAPERS_DIR = 'scrapers'


scrapers = list_scrapers(search_dir=SCRAPERS_DIR)

for scraper in scrapers:
    print(importlib.import_module(scraper))
    print(config.SCRAPER_INTERVALS[scraper])
