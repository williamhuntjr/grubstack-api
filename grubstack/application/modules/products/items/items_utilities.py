from grubstack import app

from grubstack.application.utilities.reducers import field_reducer

from .items_constants import PER_PAGE

def format_item(item: dict, ingredients_list = [], varieties_list: list = [], filters: list = []):
  json_data = {
    "id": item['item_id'],
    "name": item['name'],
    "description": item['description'],
    "thumbnail_url": item['thumbnail_url']
  }

  if 'price' in item:
    json_data['price'] = item['price']

  if 'is_onsale' in item:
    json_data['is_onsale'] = item['is_onsale']

  if 'sale_price' in item:
    json_data['sale_price'] = item['sale_price']

  if 'showIngredients' in filters and filters['showIngredients']:
    json_data['ingredients'] = ingredients_list

  if 'showVarieties' in filters and filters['showVarieties']:
    json_data['varieties'] = varieties_list

  return json_data

def format_params(params: dict, item: dict = {}):
  name = field_reducer('name', params, item, '')
  description = field_reducer('description', params, item, '')
  thumbnail_url = field_reducer('thumbnail_url', params, item, app.config['THUMBNAIL_PLACEHOLDER_IMG'])

  return (name, description, thumbnail_url)
 
def format_ingredient_params(params: dict, ingredient: dict = {}):
  is_optional = field_reducer('is_optional', params, ingredient, 'f')
  is_addon = field_reducer('is_addon', params, ingredient, 'f')
  is_extra = field_reducer('is_extra', params, ingredient, 'f')

  return (is_optional, is_addon, is_extra)