from grubstack import app, gsdb
from math import ceil

from grubstack.application.utilities.reducers import field_reducer

from .varieties_constants import PER_PAGE

def format_variety(variety: dict, ingredients_list: list = [], filters: list = []):
  json_data = {
    "id": variety['variety_id'],
    "name": variety['name'],
    "description": variety['description'],
    "thumbnail_url": variety['thumbnail_url'],
  }

  if 'showIngredients' in filters and filters['showIngredients']:
    json_data['ingredients'] = ingredients_list

  return json_data

def format_params(params: dict, variety: dict = {}):
  name = field_reducer('name', params, variety, '')
  description = field_reducer('description', params, variety, '')
  thumbnail_url = field_reducer('thumbnail_url', params, variety, app.config['THUMBNAIL_PLACEHOLDER_IMG'])

  return (name, description, thumbnail_url)