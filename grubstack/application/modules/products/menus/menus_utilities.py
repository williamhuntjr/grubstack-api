from grubstack import app, gsdb
from math import ceil

PER_PAGE = app.config['PER_PAGE']

def format_menu(menu: dict, items_list: list = [], filters: list = []):
  json_data = {
    "id": menu['menu_id'],
    "name": menu['name'],
    "description": menu['description'],
    "thumbnail_url": menu['thumbnail_url'],
    "label_color": menu['label_color'],
  }

  if 'showItems' in filters and filters['showItems']:
    json_data['items'] = items_list

  return json_data

def format_params(params: dict):
  name = params['name']
  description = params['description'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']
  label_color = params['label_color'] or 'blue'

  return (name, description, thumbnail_url, label_color)

def format_item_params(params: dict):
  price = params['price'] if 'price' in params else 0
  sale_price = params['sale_price'] if 'sale_price' in params else 0
  is_onsale = params['is_onsale'] if 'is_onsale' in params else False
  
  return (price, sale_price, is_onsale)

def getMenus(page: int = 1, limit: int = PER_PAGE):
  json_data = []
  menus = gsdb.fetchall("SELECT * FROM gs_menu ORDER BY name ASC")

  menus_list = []
  for menu in menus:
    items = gsdb.fetchall("""SELECT c.item_id, name, description, thumbnail_url, label_color, price, sale_price, is_onsale
                          FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                          WHERE p.menu_id = %s ORDER BY name ASC""", (menu['menu_id'],))
    items_list = []
    for item in items:
      items_list.append({
        "id": item['item_id'],
        "name": item['name'],
        "description": item['description'],
        "thumbnail_url": item['thumbnail_url'],
        "label_color": item['label_color'],
        "price": item['price'],
        "sale_price": item['sale_price'],
        "is_onsale": item['is_onsale']
      })
    menus_list.append(format_menu(menu, items_list))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(menus) / limit)
  total_rows = len(menus)

  # Get paged data
  json_data = menus_list[start:end]

  return (json_data, total_rows, total_pages)

def getMenuItems(menu_id, page: int = 1, limit: int = PER_PAGE):
  json_data = []
  items = gsdb.fetchall("""SELECT c.item_id, name, description, thumbnail_url, label_color, price, sale_price, is_onsale
                                  FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                                  WHERE p.menu_id = %s ORDER BY name ASC""", (menu_id,))

  items_list = []
  for item in items:
    items_list.append({
      "id": item['item_id'],
      "name": item['name'],
      "description": item['description'],
      "thumbnail_url": item['thumbnail_url'],
      "label_color": item['label_color'],
      "price": item['price'],
      "sale_price": item['sale_price'],
      "is_onsale": item['is_onsale']
    })

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(items) / limit)
  total_rows = len(items)

  # Get paged data
  json_data = items_list[start:end]

  return (json_data, total_rows, total_pages)
