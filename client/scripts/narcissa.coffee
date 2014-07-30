sevenDaysAgo = Date.today().add(-3).days().valueOf() / 1000

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
    .field('date_uts')
    .field('url')
    .order('date_uts', false)
    .limit(3)
  addictiveTracks: sprintf '
    SELECT
      fp.name AS name, fp.artist_text AS artist_text,
      fp.album_text AS album_text, fp.date_uts AS date_uts, fp.url AS url
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
    ORDER BY ap.date_uts DESC
    LIMIT 3
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
  self.type = data.type
  self.start_date = data.start_date
  self.distance_mi = sprintf '%.02f', data.distance_mi
  self.pace_mins_per_mi = min_to_m_ss(data.pace_mins_per_mi)
  self.polyline = data.polyline
  return

Track = (data) ->
  self = this
  self.name = data.name
  self.artist_text = data.artist_text
  self.album_text = data.album_text
  self.date_uts = data.date_uts
  self.url = data.url
  self.summary = ko.computed( () ->
    if self.album_text
      sprintf '%s - %s (from %s)', self.artist_text, self.name, self.album_text
    else
      sprintf '%s - %s', self.artist_text, self.name
  )
  return

Place = (data) ->
  self.place_name = data.place_name
  self.start_time = data.startTime
  self.place_lat = data.place_location_lat
  self.place_lon = data.place_location_lon
  self.here_since = ko.computed( () ->
    $.timeago new Date self.start_time
  )
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
      _.each(_.pairs(data), (pair) ->
        name = pair[0]
        queryTime = pair[1].query_time_sec
        if queryTime
          console.log sprintf '%s: query took %.3f sec', name, queryTime
        else
          console.log sprintf '%s: cached', name
        return
      )
      self.showUI true

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

  ).fail (jqXHR) ->
    console.log jqXHR.status, jqXHR.statusText, jqXHR.responseText
    return
  return

ko.applyBindings new NarcissaViewModel()
