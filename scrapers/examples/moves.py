scheduler = globals()['scheduler']


def scrape_moves():
    # Scraper config:

    # Enter your Moves app info here.
    # You can find this at https://dev.moves-app.com/apps
    # Yes, the client secret is Very Long.
    CLIENT_ID = 'B1E55EDB1F0CA15'
    CLIENT_SECRET = 'OFF1C1A15CAFF01D'
    # Moves auth callbacks will hit this host and port. Change the port if you
    # need to avoid port conflicts with other servers.
    # Configure your Redirect URI in https://dev.moves-app.com/apps to match
    # your host and port.
    CALLBACK_PORT = 61902
    # Where to store your Moves places info and the Moves auth token.
    PLACES_TABLE = 'moves_places'
    TOKEN_TABLE = 'moves_token'

    # Scraper body begins here.

    import config

    import collections
    import json
    import webbrowser
    from dateutil.parser import parse
    from cgi import parse_qs
    from wsgiref.simple_server import make_server

    import dataset
    import requests
    from pytz import utc

    MOVES_AUTH_URL = ('https://api.moves-app.com/oauth/v1/authorize?'
                      'response_type=code&client_id=%s&scope=%s')
    MOVES_TOKEN_URL = ('https://api.moves-app.com/oauth/v1/access_token?'
                       'grant_type=authorization_code&code=%s&client_id=%s&'
                       'client_secret=%s&redirect_uri=%s')
    MOVES_API_BASE_URL = 'https://api.moves-app.com/api/1.1'
    MOVES_SCOPE = 'activity%20location'
    FSQ_PROP = 'place_foursquareCategoryIds'

    def get_new_token():
        authorize_url = MOVES_AUTH_URL % (CLIENT_ID, MOVES_SCOPE)
        webbrowser.open(authorize_url)
        print('Click here to authorize me to access your Moves data: %s'
              % authorize_url)
        make_server('localhost', CALLBACK_PORT, auth_listener).handle_request()

    def auth_listener(environ, start_response):
        start_response("200 OK", [('Content-Type', 'text/plain')])
        parameters = parse_qs(environ.get('QUERY_STRING', ''))
        if 'error' in parameters:
            err = ('Moves returned an error: %s' % parameters['error'][0]
                   + '. I can\'t access your data.')
            print(err)
            return [err.encode('utf-8')]
        if 'code' not in parameters:
            err = ('Moves didn\'t return an auth code. '
                   'I can\'t access your data.')
            print(err)
            return [err.encode('utf-8')]
        code_received(parameters['code'][0])
        return ['Got your authorization from Moves! '
                'You can close this window now.'
                .encode('utf-8')]

    def get_auth_from_code(code):
        callback_url = '%s:%s' % (config.SERVER_HOST, CALLBACK_PORT)
        resp = requests.post(MOVES_TOKEN_URL %
                             (code, CLIENT_ID, CLIENT_SECRET,
                              callback_url)).json()
        if 'error' in resp:
            raise ValueError('Received error when requesting access token: '
                             '%s' % resp['error'])
        if 'access_token' not in resp:
            raise ValueError('No access token received')
        return resp

    def code_received(code):
        auth = get_auth_from_code(code)
        token = auth['access_token']
        refresh = auth['refresh_token']
        tokens.insert({'token': token, 'refresh': refresh})
        print('Got your authorization from Moves. Thanks!')
        query_moves(token)

    def moves_get(path, token):
        if path.find('?'):
            delim = '&'
        else:
            delim = '?'
        return requests.get(MOVES_API_BASE_URL + path +
                            '%saccess_token=%s' % (delim, token)).json()

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

    def query_moves(token):
        print('Querying Moves...')

        table = db[PLACES_TABLE]
        days = moves_get('/user/places/daily?pastDays=31', token)
        recentDays = sorted(days, key=lambda item: item['date'], reverse=True)

        all_segments = []
        segment_start_times = set()

        for day in recentDays:
            # Sometimes day['segments'] is null. Make sure we catch that.
            # I'm surprised Moves API returns days without segments.
            if not day['segments']:
                continue
            for segment in day['segments']:
                # Parse then rewrite times as UTC to ensure they're consistent
                for prop in ['startTime', 'lastUpdate', 'endTime']:
                    dirty_dt = parse(segment[prop])
                    clean_dt = utc.normalize(dirty_dt.astimezone(utc))
                    segment[prop] = clean_dt.isoformat()
                segment = flatten(segment)
                # Dedupe: some segments appear in multiple days
                if segment['startTime'] in segment_start_times:
                    continue
                # Flatten foursquareCategoryIds lists
                if FSQ_PROP in segment:
                    segment[FSQ_PROP] = json.dumps(segment[FSQ_PROP])
                segment_start_times.add(segment['startTime'])
                all_segments.append(segment)

        num_segments = len(all_segments)
        recent_segments = sorted(all_segments,
                                 key=lambda seg: parse(seg['startTime']),
                                 reverse=True)

        segments_added = 0
        segments_updated = 0
        for segment in recent_segments:
            existing = table.find_one(startTime=segment['startTime'])
            if existing:
                existing_updated = parse(existing['lastUpdate'])
                segment_updated = parse(segment['lastUpdate'])
                if segment_updated > existing_updated:
                    segments_updated += 1
                    segment['id'] = existing['id']
                    table.update(segment, ['id'])
            else:
                segments_added += 1
                table.insert(segment)

        print('Done! Added %s and updated %s segments (out of %s total).' %
              (segments_added, segments_updated, num_segments))

    db = dataset.connect(config.DB_URI)
    tokens = db[TOKEN_TABLE]
    token_obj = tokens.find_one()

    if token_obj:
        token = token_obj['token']
        query_moves(token)
    else:
        get_new_token()

# From https://dev.moves-app.com/docs/api:
# An unpublished app can make at most 2000 requests per hour and 60 requests
# per minute. For apps published in Connected Apps, the limits are 4000
# requests per hour and 120 requests per minute.
scheduler.every(1).minutes.do(scrape_moves)
