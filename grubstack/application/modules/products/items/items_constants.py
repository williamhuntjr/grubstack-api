from grubstack import app

PER_PAGE = app.config['PER_PAGE']

REQUIRED_FIELDS = [
  'name',
  'slug'
]
ITEM_FILTERS = ['showVarieties', 'showIngredients']
DEFAULT_FILTERS = {
  'showIngredients': True,
  'showVarieties': False
}