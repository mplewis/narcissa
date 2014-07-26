#!/usr/bin/env python3

import os
from os import path


def list_scrapers(search_dir='.'):
    valid_scrapers = []
    possible_scraper_dirs = [n for n in os.listdir(search_dir)
                             if path.isdir(path.join(search_dir, n))]

    for d in possible_scraper_dirs:
        d_path = path.join(search_dir, d)
        for f in os.listdir(d_path):
            fn, ext = path.splitext(f)
            if d == fn and ext == '.py':
                valid_scrapers.append(d)

    return valid_scrapers


if __name__ == '__main__':
    print(list_scrapers())
