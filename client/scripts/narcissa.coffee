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

ActivityListViewModel = () ->
  self = this
  self.activities = ko.observableArray []
  
  $.post(
    'http://localhost:5000/'
    {'query': queryStrings.activities}
    (data) ->
      mappedActivities = _.map data.results, (result) ->
        new Activity(result)
      self.activities(mappedActivities)
      return
  )

  return

ko.applyBindings new ActivityListViewModel()
