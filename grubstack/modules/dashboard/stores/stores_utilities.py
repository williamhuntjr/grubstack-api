from grubstack import app, gsdb
from math import ceil

PER_PAGE = app.config['PER_PAGE']

def formatStore(store: dict, menus_list: list):
  return {
    "id": store['store_id'],
    "name": store['name'],
    "address1": store['address1'],
    "city": store['city'],
    "state": store['state'],
    "postal": store['postal'],
    "store_type": store['store_type'],
    "thumbnail_url": store['thumbnail_url'],
    "phone_number": store['phone_number'],
    "menus": menus_list
  }

def formatParams(params: dict):
  name = params['name']
  address1 = params['address1'] or ''
  city = params['city'] or ''
  state = params['state'] or ''
  postal = params['postal'] or ''
  store_type = params['store_type'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']
  phone_number = params['phone_number'] or ''

  return (name, address1, city, state, postal, store_type, thumbnail_url, phone_number)

def getStores(page: int = 1, limit: int = PER_PAGE):
  json_data = []
  stores = gsdb.fetchall("SELECT * FROM gs_store ORDER BY name ASC")
  
  stores_list = []
  for store in stores:
    menus = gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url
                              FROM gs_menu c INNER JOIN gs_store_menu p ON p.menu_id = c.menu_id 
                              WHERE p.store_id = %s ORDER BY name ASC""", (store['store_id'],))
    menus_list = []
    if menus != None:
      for menu in menus:
        menus_list.append({
          "id": menu['menu_id'],
          "name": menu['name'],
          "description": menu['description'],
          "thumbnail_url": menu['thumbnail_url'],
        })

    stores_list.append(formatStore(store, menus_list))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(stores) / limit)
  total_rows = len(stores)

  json_data = stores_list[start:end]
  return (json_data, total_rows, total_pages)

def getStoreMenus(storeId, page: int = 1, limit: int = PER_PAGE):
  json_data = []
  menus = gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url
                          FROM gs_menu c INNER JOIN gs_store_menu p ON p.menu_id = c.menu_id 
                          WHERE p.store_id = %s ORDER BY name ASC""", (storeId,))

  menus_list = []
  if menus != None:
    for menu in menus:
      menus_list.append({
        "id": menu['menu_id'],
        "name": menu['name'],
        "description": menu['description'],
        "thumbnail_url": menu['thumbnail_url'],
      })

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(menus) / limit)
  total_rows = len(menus)
  
  # Get paged data
  json_data = menus_list[start:end]

  return (json_data, total_rows, total_pages)