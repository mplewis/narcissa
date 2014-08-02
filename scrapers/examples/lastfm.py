scheduler = globals()['scheduler']


def scrape_lastfm():
    # Scraper config:

    # Enter your own Last.fm username here.
    USERNAME = 'trickybeta'
    # Get your app's API key from http://www.last.fm/api/accounts.
    API_KEY = 'c0ffeecafefacade'
    # Tracks to retrieve per page request. Max 200.
    # Recommended: 200 for the first run, 10 after that.
    # Leaving this at 200 makes Last.fm requests really slow.
    PER_PAGE = 200
    # Where to store your Last.fm track info.
    DB_TABLE = 'lastfm_tracks'

    # Scraper body begins here.

    import config
    import collections
    import dataset
    import requests

    api_url = ('http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&'
               'user=%s&api_key=%s&format=json&page=%s&limit=%s')

    def recent_tracks(user, page, limit):
        """
        Get the most recent tracks from `user` using `api_key`.
        Start at page `page` and limit results to `limit`.
        """
        return requests.get(api_url % (user, API_KEY, page, limit)).json()

    def flatten(d, parent_key=''):
        """
        From http://stackoverflow.com/a/6027615/254187.
        Modified to strip # symbols from dict keys.
        """
        items = []
        for k, v in d.items():
            new_key = parent_key + '_' + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(flatten(v, new_key).items())
            else:
                # Strip pound symbols from column names
                new_key = new_key.replace('#', '')
                items.append((new_key, v))
        return dict(items)

    def process_track(track):
        """
        Removes `image` keys from track data.
        Replaces empty strings for values with None.
        """
        if 'image' in track:
            del track['image']
        flattened = flatten(track)
        for key, val in flattened.items():
            if val == '':
                flattened[key] = None
        return flattened

    def add_page_tracks(page, table):
        """
        Iterate through all tracks on a page and add each track to the given
        table. Skip tracks that already exist.

        Returns a dict with metadata:
        {
            'num_added': The number of tracks added to the table.
            'num_skipped': The number of tracks on the page that already
                existed in the table and were skipped.
            'num_invalid': The number of tracks without a `date_uts` property.
        }
        """

        num_added = 0
        num_skipped = 0
        num_invalid = 0

        try:
            for raw_track in page['recenttracks']['track']:
                track = process_track(raw_track)

                if 'date_uts' not in track:
                    num_invalid += 1
                elif table.find_one(date_uts=track['date_uts']):
                    num_skipped += 1
                else:
                    table.insert(track)
                    num_added += 1
        except Exception:
            print(page)

        return {'num_added': num_added,
                'num_skipped': num_skipped,
                'num_invalid': num_invalid}

    def scrape_page(page_num):
        """
        Scrape the page at the given page number and return the results of
        adding all tracks from add_page_tracks.
        """
        return recent_tracks(USERNAME, page_num, PER_PAGE)

    print('Querying Last.fm...')

    db = dataset.connect(config.DB_URI)
    tracks = db[DB_TABLE]

    # We need to get the first page so we can find out how many total pages
    # there are in our listening history.
    print('Page', 1, 'of <unknown>')
    page = scrape_page(0)
    total_pages = int(page['recenttracks']['@attr']['totalPages'])
    results = add_page_tracks(page, tracks)

    tracks_added = results['num_added']
    total_tracks_added = tracks_added
    tracks_were_added = tracks_added > 0

    print('%s track(s) added.' % tracks_added)

    for page_num in range(1, total_pages + 1):
        while tracks_were_added:
            print('Page', page_num + 1, 'of', total_pages)
            page = scrape_page(page_num)
            results = add_page_tracks(page, tracks)

            tracks_added = results['num_added']
            total_tracks_added += tracks_added
            tracks_were_added = tracks_added > 0

            print('%s track(s) added.' % tracks_added)

    # Confirm our tracks were inserted into the database
    print('Done! %s track(s) added.' % total_tracks_added)


# Last.fm allows 1 request per second.
scheduler.every(1).minutes.do(scrape_lastfm)
