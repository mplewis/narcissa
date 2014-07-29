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
  addictiveTracks: '
    SELECT
      fp.name AS name, fp.artist_text AS artist_text,
      fp.album_text AS album_text, fp.date_uts AS date_uts, fp.url AS url
    FROM
      (SELECT * FROM lastfm_tracks GROUP BY url ORDER BY date_uts) fp
    INNER JOIN lastfm_tracks ap ON
      fp.url = ap.url AND
      ap.date_uts - fp.date_uts <= (86400 * 7)
    GROUP BY ap.url
    HAVING COUNT(ap.url) > 3
    ORDER BY ap.date_uts DESC
    LIMIT 5
  '
}

queryStrings = {}
_.each(_.pairs(queries), (pair) ->
  name = pair[0]
  queryString = pair[1].toString()
  queryStrings[name] = queryString
  console.log 'queryStrings.' + name + ':', queryString
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
    sprintf('%s, %s, %s', self.type, self.name, self.start_date)
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
    if (self.album_text)
      sprintf('%s - %s (from %s)', self.artist_text, self.name, self.album_text)
    else
      sprintf('%s - %s', self.artist_text, self.name)
  )
  return

NarcissaViewModel = () ->
  self = this
  
  self.activities = ko.observableArray []
  self.recentTracks = ko.observableArray []
  self.addictiveTracks = ko.observableArray []
  
  $.post(
    'http://localhost:5000/'
    {
      'activities': queryStrings.activities,
      'recentTracks': queryStrings.recentTracks,
      'addictiveTracks': queryStrings.addictiveTracks
    }
    (data) ->
      console.log data
      self.activities(_.map data.activities.results, (result) -> new Activity(result))
      self.recentTracks(_.map data.recentTracks.results, (result) -> new Track(result))
      self.addictiveTracks(_.map data.addictiveTracks.results, (result) -> new Track(result))
      return
  ).fail (jqXHR) ->
    console.log jqXHR.status, jqXHR.statusText, jqXHR.responseText
    return

  return

ko.applyBindings new NarcissaViewModel()
