from grubstack import app

PER_PAGE = app.config['PER_PAGE']

REQUIRED_FIELDS = [
  'name'
]
VARIETY_FILTERS = ['showIngredients']
DEFAULT_FILTERS = {
  'showIngredients': False
}