scheduler = globals()['scheduler']


def scrape_github():
    """
    Scrape a user's GitHub events and commits.
    """

    # The GitHub user to scrape
    GITHUB_USER = 'mplewis'

    # You can scrape GitHub without an application token/secret, but you'll be
    # limited to 60 reqs/hour. Get application credentials at
    # https://github.com/settings/applications.
    CLIENT_ID = 'ED1F1ED0FF1CE5'
    CLIENT_SECRET = 'C1A551F1AB1ED15EA5E'
    # Set this to False to use GitHub's unauthenticated API.
    USE_AUTH = True
    # Where to store your GitHub event and commit info.
    EVENTS_TABLE = 'github_events'
    COMMITS_TABLE = 'github_commits'

    # Scraper code starts here.

    import config

    import collections
    import json

    import dataset
    import requests

    GITHUB_API_URL = 'https://api.github.com/users/%s/events/public?page=%s'

    def flatten(d, parent_key='', sep='_'):
        """
        From http://stackoverflow.com/a/6027615/254187.
        """
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(flatten(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def fetch_events(page):
        """Retrieve one page of GitHub user event data."""
        req_url = GITHUB_API_URL % (GITHUB_USER, page)
        if USE_AUTH:
            req_url = (req_url +
                       '&client_id=%s&client_secret=%s' %
                       (CLIENT_ID, CLIENT_SECRET))
        return requests.get(req_url).json()

    print('Querying GitHub...')

    db = dataset.connect(config.DB_URI)
    events_table = db[EVENTS_TABLE]
    commits_table = db[COMMITS_TABLE]

    events_added = 0
    commits_added = 0
    page = 1
    found_existing = False
    while page <= 10 and not found_existing:
        print('Page %s of 10' % page)
        # Fetch a page of events, flatten it, and process it
        events = fetch_events(page)
        events_flat = [flatten(e) for e in events]
        for event in events_flat:
            # Stop when we hit an event that exists
            if events_table.find_one(event_id=event['id']):
                found_existing = True
                break

            # Break commits list into its own object
            if 'payload_commits' in event:
                commits = event.pop('payload_commits')
            else:
                commits = None

            # Sanitize all lists on the flattened event into JSON before
            # storage
            for k in event.keys():
                if type(event[k]) is list:
                    event[k] = json.dumps(event[k])

            # Rename id to event_id so SQLite can assign its own row ID
            event['event_id'] = event.pop('id')
            events_table_id = events_table.insert(event)
            events_added += 1

            # Add commits to commit table and reference their events' row IDs
            if commits:
                for commit in commits:
                    commit_flat = flatten(commit)
                    commit_flat['event_id'] = events_table_id
                    commits_table.insert(commit_flat)
                commits_added += len(commits)

        page += 1

    print('Done! %s events and %s commits added.' % (events_added,
                                                     commits_added))

# GitHub allows 5000 authenticated or 60 unauthenticated requests per hour.
scheduler.every(60).seconds.do(scrape_github)
