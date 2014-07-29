Activity = (data) ->
  self = this
  self.name = data.name

ActivityListViewModel = () ->
  self = this
  self.activities = ko.observableArray []
  
  $.post(
    'http://localhost:5000/'
    {'query': 'SELECT * FROM strava_activities'}
    (data) ->
      mappedActivities = _.map data.results, (result) ->
        new Activity(result)
      self.activities(mappedActivities)
      return
  )

  return

ko.applyBindings new ActivityListViewModel()
