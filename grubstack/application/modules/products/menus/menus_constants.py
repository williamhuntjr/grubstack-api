from grubstack import app

PER_PAGE = app.config['PER_PAGE']

REQUIRED_FIELDS = [
  'name',
  'slug'
]
MENU_FILTERS = ['showItems']
DEFAULT_FILTERS = {
  'showItems': True,
}