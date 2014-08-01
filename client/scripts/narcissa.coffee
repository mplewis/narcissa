API_URLS = {
  lastfm: {
    getAlbumArt: 'http://ws.audioscrobbler.com/2.0/?' +
      'method=album.getinfo&api_key=%s&artist=%s&album=%s&format=json'
  }
}

API_KEYS = {
  lastfm: 'daadd05b0eefdbcfac9df552e5d90a86'
}

PLACEHOLDERS = {
  album: '/images/unknown_album.png'
}

sevenDaysAgo = Date.today().add(-7).days().valueOf() / 1000
console.log sevenDaysAgo

min_to_m_ss = (min_frac) ->
  sprintf '%d:%02d', Math.floor(min_frac), 60 * (min_frac % 1)

queries = {
  currentPlace: squel.select()
    .from('moves_places')
    .field('startTime')
    .field('place_name')
    .field('place_location_lat')
    .field('place_location_lon')
    .order('startTime', false)
    .limit(1)
  lastActivity: squel.select()
    .from('strava_activities')
    .field('name')
    .field('type')
    .field('start_date')
    .field('distance_mi')
    .field('pace_mins_per_mi')
    .field('polyline')
    .order('start_date', false)
    .limit(1)
  recentTracks: squel.select()
    .from('lastfm_tracks')
    .field('name')
    .field('artist_text')
    .field('album_text')
    .field('album_mbid')
    .field('date_uts')
    .field('url')
    .order('date_uts', false)
    .limit(5)
  addictiveTracks: sprintf '
    SELECT COUNT(fp.url) AS plays, fp.date_uts AS date_uts,
      fp.artist_text AS artist_text, fp.name AS name,
      fp.album_text AS album_text, fp.url AS url
      FROM
        (SELECT * FROM lastfm_tracks GROUP BY url ORDER BY date_uts) fp
    INNER JOIN lastfm_tracks ap ON
      fp.url = ap.url AND
      ap.date_uts - fp.date_uts <= (86400 * 7)
    WHERE
      ap.date_uts > %(earliestDate)s AND
      fp.date_uts > %(earliestDate)s
    GROUP BY ap.url
    HAVING COUNT(ap.url) > 3
    ORDER BY plays DESC
    LIMIT 5
  ', {earliestDate: sevenDaysAgo}
}

queryStrings = {}
_.each(_.pairs(queries), (pair) ->
  name = pair[0]
  queryString = pair[1].toString()
  queryStrings[name] = queryString
  return
)

Activity = (data) ->
  self = this
  self.name = data.name
  self.type = data.type.toLowerCase()
  self.start_date = data.start_date
  self.distance_mi = sprintf '%.01f', data.distance_mi
  self.pace_mins_per_mi = min_to_m_ss(data.pace_mins_per_mi)
  self.polyline = data.polyline
  return

Track = (data) ->
  console.log data
  self = this
  self.name = data.name
  self.artist_text = data.artist_text
  self.album_text = data.album_text
  self.album_mbid = data.album_mbid
  self.plays = data.plays || 1
  self.played_at = new Date((data.date_uts * 1000)).toISOString()
  self.url = data.url
  return

Place = (data) ->
  self.place_name = data.place_name
  self.start_time = data.startTime
  self.place_lat = data.place_location_lat
  self.place_lon = data.place_location_lon
  return

NarcissaViewModel = () ->
  self = this

  self.showUI = ko.observable false

  self.about = ko.observable()

  self.currentPlace = ko.observable()
  self.lastActivity = ko.observable()
  self.recentTracks = ko.observableArray []
  self.addictiveTracks = ko.observableArray []

  $.get(
    '/data/whoami.json'
    (data) ->
      console.log data
  )

  $.post(
    'http://localhost:5000/'
    {
      'currentPlace': queryStrings.currentPlace
      'lastActivity': queryStrings.lastActivity,
      'recentTracks': queryStrings.recentTracks,
      'addictiveTracks': queryStrings.addictiveTracks,
    }
    (data) ->
      self.currentPlace new Place data.currentPlace.results[0]
      self.lastActivity new Activity data.lastActivity.results[0]
      self.recentTracks(_.map data.recentTracks.results,
                        (result) -> new Track result)
      self.addictiveTracks(_.map data.addictiveTracks.results,
                           (result) -> new Track result)

      self.showUI true

      for pair in _.pairs(data)
        do (pair) ->
          name = pair[0]
          queryTime = pair[1].query_time_sec
          if queryTime
            console.log sprintf '%s: query took %.3f sec', name, queryTime
          else
            console.log sprintf '%s: cached', name
          return

      allTracks = []
      allTracks.push(track) for track in self.recentTracks()
      allTracks.push(track) for track in self.addictiveTracks()
      uniqueTracks = _.uniq allTracks, false, (track) ->
        track.artist_text + '!?&*#' + track.album_text

      currPlaceMap = L.mapbox.map 'map-current-place', 'mplewis.j3i59a6a'
      lastWorkoutMap = L.mapbox.map 'map-last-workout', 'mplewis.j3i59a6a'

      rawCurrPlace = data.currentPlace.results[0]
      rawLastAct = data.lastActivity.results[0]

      currPlace = [rawCurrPlace.place_location_lat,
                   rawCurrPlace.place_location_lon]

      currPlaceMap.setView currPlace, 14
      L.marker(currPlace).addTo(currPlaceMap)

      workoutPoly = L.Polyline.fromEncoded(
        rawLastAct.polyline, {color: 'teal'}).addTo lastWorkoutMap
      lastWorkoutMap.fitBounds(workoutPoly.getBounds())

      return

  ).fail (jqXHR) ->
    console.log jqXHR.status, jqXHR.statusText, jqXHR.responseText
    return
  return

# From http://stackoverflow.com/a/11270500/254187
ko.bindingHandlers.timeago = update: (element, valueAccessor) ->
  value = ko.utils.unwrapObservable(valueAccessor())
  $this = $(element)
  # Set the title attribute to the new value = timestamp
  $this.attr "title", value

  # If timeago has already been applied to this node, don't reapply it -
  # since timeago isn't really flexible (it doesn't provide a public
  # remove() or refresh() method) we need to do everything by ourselves.
  if $this.data("timeago")
    datetime = $.timeago.datetime($this)
    distance = (new Date().getTime() - datetime.getTime())
    inWords = $.timeago.inWords(distance)
    # Update cache and displayed text..
    $this.data "timeago",
      datetime: datetime
    $this.text inWords

  else
    # timeago hasn't been applied to this node -> we do that now!
    $this.timeago()

  return

ko.applyBindings new NarcissaViewModel()
