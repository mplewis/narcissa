scheduler = globals()['scheduler']


def scrape_strava():
    import config

    import webbrowser
    import logging
    from cgi import parse_qs
    from wsgiref.simple_server import make_server

    import dataset
    from stravalib.client import Client
    from stravalib import unithelper
    from units import unit

    # Enter your Strava API info here.
    # You can find this at https://www.strava.com/settings/api
    CLIENT_ID = 31337
    CLIENT_SECRET = 'BA5ED60D'

    # Pick your DB table names here.
    ACTIVITIES_TABLE = 'strava_activities'
    TOKEN_TABLE = 'strava_token'

    # Strava auth callbacks will hit this host and port. Change the port if you
    # need to avoid port conflicts with other servers.
    CALLBACK_HOST = 'http://localhost'
    CALLBACK_PORT = 36724

    # And here's the rest of the scraper.

    def get_new_token():
        authorize_url = client.authorization_url(
            client_id=CLIENT_ID,
            redirect_uri=('%s:%s' % (CALLBACK_HOST, CALLBACK_PORT))
        )
        webbrowser.open(authorize_url)
        print('Click here to authorize me to access your Strava activities: %s'
              % authorize_url)
        make_server('localhost', CALLBACK_PORT, auth_listener).handle_request()

    def auth_listener(environ, start_response):
        start_response("200 OK", [('Content-Type', 'text/plain')])
        parameters = parse_qs(environ.get('QUERY_STRING', ''))
        code_received(parameters['code'][0])
        return ['Got your authorization from Strava! '
                'You can close this window now.'
                .encode('utf-8')]

    def code_received(code):
        token = client.exchange_code_for_token(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               code=code)
        tokens.insert({'token': token})
        print('Got your authorization from Strava. Thanks!')
        query_strava()

    def avg_speed_to_mins(avg_speed):
        sec_per_meter = unit('s') / unit('m')
        min_per_mile = unit('min') / unit('mi')
        pace = min_per_mile(sec_per_meter(avg_speed.get_num() ** -1))
        return pace.get_num()

    def query_strava():
        print('Querying Strava...')

        table = db[ACTIVITIES_TABLE]
        activity_summaries = [a for a in client.get_activities()]
        num_added = 0

        for a_summary in activity_summaries:
            if table.find_one(strava_id=a_summary.id):
                break
            a = client.get_activity(a_summary.id)
            activity_data = {
                'strava_id': a.id,
                'name': a.name,
                'type': a.type,
                'start_date': a.start_date.isoformat(),
                'distance_mi': float(unithelper.miles(a.distance)),
                'elapsed_sec': a.elapsed_time.total_seconds(),
                'pace_mins_per_mi': avg_speed_to_mins(a.average_speed),
                'polyline': a.map.summary_polyline
            }
            print('Added %s: %s' % (a.type, a.name))
            num_added += 1
            table.insert(activity_data)

        print('Done! %s activities added.' % num_added)

    # Stravalib throws lots of warnings for schema issues on Strava's end.
    # These warnings don't impact us so let's ignore them.
    logger_names = [k for k in logging.Logger.manager.loggerDict.keys() if
                    k.startswith('stravalib')]
    for logger_name in logger_names:
        logging.getLogger(logger_name).setLevel(logging.ERROR)

    client = Client()

    db = dataset.connect(config.DB_URI)
    tokens = db[TOKEN_TABLE]
    token_obj = tokens.find_one()

    if token_obj:
        client.access_token = token_obj['token']
        query_strava()
    else:
        get_new_token()


scheduler.every(10).minutes.do(scrape_strava)
scrape_strava()
