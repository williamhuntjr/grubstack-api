from math import ceil

from grubstack import app, gsdb

PER_PAGE = app.config['PER_PAGE']

def format_store(store: dict, menus_list: list = [], filters: list = []):
  json_data = {
    "id": store['store_id'],
    "name": store['name'],
    "address1": store['address1'],
    "city": store['city'],
    "state": store['state'],
    "postal": store['postal'],
    "store_type": store['store_type'],
    "thumbnail_url": store['thumbnail_url'],
    "phone_number": store['phone_number'],
  }
  if 'showMenus' in filters and filters['showMenus']:
    json_data['menus'] = menus_list

  return json_data

def format_params(params: dict):
  name = params['name']
  address1 = params['address1'] or ''
  city = params['city'] or ''
  state = params['state'] or ''
  postal = params['postal'] or ''
  store_type = params['store_type'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']
  phone_number = params['phone_number'] or ''

  return (name, address1, city, state, postal, store_type, thumbnail_url, phone_number)