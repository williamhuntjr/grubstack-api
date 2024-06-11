from grubstack import app

PER_PAGE = app.config['PER_PAGE']

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
LOCATION_FILTERS = ['showMenus', 'showItems', 'isActive']
DEFAULT_FILTERS = {
  'showMenus': False,
  'showItems': False,
  'isActive': True
}