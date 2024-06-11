from grubstack import app, gsdb
from math import ceil

PER_PAGE = app.config['PER_PAGE']

def format_menu(menu: dict, items_list: list = [], filters: list = []):
  json_data = {
    "id": menu['menu_id'],
    "name": menu['name'],
    "description": menu['description'],
    "thumbnail_url": menu['thumbnail_url'],
  }

  if 'showItems' in filters and filters['showItems']:
    json_data['items'] = items_list

  return json_data

def format_params(params: dict):
  name = params['name']
  description = params['description'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']

  return (name, description, thumbnail_url)

def format_item_params(params: dict):
  price = params['price'] if 'price' in params else 0
  sale_price = params['sale_price'] if 'sale_price' in params else 0
  is_onsale = params['is_onsale'] if 'is_onsale' in params else False
  
  return (price, sale_price, is_onsale)

def format_menu_item(item: dict):
  json_data = {
    "id": item['item_id'],
    "name": item['name'],
    "description": item['description'],
    "thumbnail_url": item['thumbnail_url'],
    "price": item['price'],
    "sale_price": item['sale_price'],
    "is_onsale": item['is_onsale']
  }
  return json_data