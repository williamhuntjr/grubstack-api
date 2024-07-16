from grubstack import app

from grubstack.application.utilities.reducers import field_reducer

from .menus_constants import PER_PAGE

def format_menu(menu: dict, items_list: list = [], filters: list = []):
  json_data = {
    "id": menu['menu_id'],
    "name": menu['name'],
    "description": menu['description'],
    "thumbnail_url": menu['thumbnail_url'],
    "slug": menu['slug']
  }

  if 'showItems' in filters and filters['showItems']:
    json_data['items'] = items_list

  return json_data

def format_params(params: dict, menu: dict = {}):
  name = field_reducer('name', params, menu, '')
  description = field_reducer('description', params, menu, '')
  thumbnail_url = field_reducer('thumbnail_url', params, menu, app.config['THUMBNAIL_PLACEHOLDER_IMG'])
  slug = field_reducer('slug', params, menu, '')

  return (name, description, thumbnail_url, slug)

def format_item_params(params: dict, item: dict = {}):
  price = field_reducer('price', params, item, 'f')
  sale_price = field_reducer('sale_price', params, item, 'f')
  is_onsale = field_reducer('is_onsale', params, item, 'f')

  return (price, sale_price, is_onsale)