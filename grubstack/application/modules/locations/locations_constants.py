from grubstack import app

DEFAULT_LOCATION_LIMIT = 1
REQUIRED_FIELDS = [
  'name',
  'address1',
  'city',
  'state',
  'postal',
  'location_type',
  'phone_number'
]
PER_PAGE = app.config['PER_PAGE']
LOCATION_FILTERS = ['showMenus']
DEFAULT_FILTERS = {
  'showMenus': True,
  'showItems': True
}