sevenDaysAgo = Date.today().add(-3).days().valueOf() / 1000

queries = {
  activities: squel.select()
    .from('strava_activities')
    .field('name')
    .field('type')
    .field('start_date')
    .field('distance_mi')
    .field('pace_mins_per_mi')
    .field('polyline')
    .order('start_date', false)
    .limit(3)
  recentTracks: squel.select()
    .from('lastfm_tracks')
    .field('name')
    .field('artist_text')
    .field('album_text')
    .field('date_uts')
    .field('url')
    .order('date_uts', false)
    .limit(5)
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
    LIMIT 5
  ', {earliestDate: sevenDaysAgo}
  currentPlace: squel.select()
    .from('moves_places')
    .field('startTime')
    .field('place_name')
    .field('place_location_lat')
    .field('place_location_lon')
    .order('startTime', false)
    .limit(1)
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
  self.distance_mi = data.distance_mi
  self.pace_mins_per_mi = data.pace_mins_per_mi
  self.polyline = data.polyline
  self.summary = ko.computed( () ->
    ago = $.timeago new Date self.start_date
    pace_min_sec =
      sprintf '%02d:%02d',
      Math.floor(self.pace_mins_per_mi),
      60 * (self.pace_mins_per_mi % 1)
    sprintf '%s, %s, %s, %s/mi',
      self.type, self.name, ago, pace_min_sec
  )
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
  
  self.activities = ko.observableArray []
  self.recentTracks = ko.observableArray []
  self.addictiveTracks = ko.observableArray []
  self.currentPlace = ko.observable()
  
  $.post(
    'http://localhost:5000/'
    {
      'activities': queryStrings.activities,
      'recentTracks': queryStrings.recentTracks,
      'addictiveTracks': queryStrings.addictiveTracks,
      'currentPlace': queryStrings.currentPlace
    }
    (data) ->
      self.activities(_.map data.activities.results,
                      (result) -> new Activity(result))
      self.recentTracks(_.map data.recentTracks.results,
                        (result) -> new Track(result))
      self.addictiveTracks(_.map data.addictiveTracks.results,
                           (result) -> new Track(result))
      self.currentPlace new Place data.currentPlace.results[0]
      _.each(_.pairs(data), (pair) ->
        name = pair[0]
        queryTime = pair[1].query_time_sec
        console.log sprintf '%s: %.3f sec', name, queryTime
        return
      )
      return
  ).fail (jqXHR) ->
    console.log jqXHR.status, jqXHR.statusText, jqXHR.responseText
    return

  return

ko.applyBindings new NarcissaViewModel()
