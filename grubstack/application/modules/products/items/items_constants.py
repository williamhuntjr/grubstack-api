from grubstack import app

PER_PAGE = app.config['PER_PAGE']

REQUIRED_FIELDS = [
  'name'
]
ITEM_FILTERS = ['showVarieties', 'showIngredients']
DEFAULT_FILTERS = {
  'showIngredients': True,
  'showVarieties': True
}