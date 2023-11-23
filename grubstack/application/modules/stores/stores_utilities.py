from grubstack import app, gsdb
from math import ceil
from grubstack.application.modules.products.menus.menus_utilities import formatMenu
from grubstack.application.modules.products.items.items_utilities import formatItem
from grubstack.application.utilities.database import getStoreMenus, getMenuItems

PER_PAGE = app.config['PER_PAGE']

def formatStore(store: dict, menus_list: list = [], filters: list = []):
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

def getStore(store_id: int, filters: list = []):
  json_data = []
  store = gsdb.fetchone("SELECT * FROM gs_store WHERE store_id = %s", (store_id,))
  menus_list = []

  if 'showMenus' in filters and filters['showMenus']:
    menus = getStoreMenus(store_id)

    if menus != None:
      for menu in menus:
        items_list = []

        if 'showItems' in filters and filters['showItems']:
          items = getMenuItems(menu['menu_id'])

          for item in items:
            items_list.append(formatItem(item, []))
            
        menus_list.append(formatMenu(menu, items_list, filters))
      
  return formatStore(store, menus_list, filters)

def getStores(page: int = 1, limit: int = PER_PAGE, filters: list = []):
  json_data = []
  stores = gsdb.fetchall("SELECT * FROM gs_store ORDER BY name ASC")
  
  stores_list = []
  for store in stores:
    menus_list = []

    if 'showMenus' in filters and filters['showMenus']:
      menus = getStoreMenus(store['store_id'])

      if menus != None:
        for menu in menus:
          items_list = []

          if 'showItems' in filters and filters['showItems']:
            print(menu)
            items = getMenuItems(menu['menu_id'])
                    
            for item in items:
              items_list.append(formatItem(item))

          menus_list.append(formatMenu(menu, items_list, filters))

    stores_list.append(formatStore(store, menus_list, filters))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(stores) / limit)
  total_rows = len(stores)

  json_data = stores_list[start:end]
  return (json_data, total_rows, total_pages)

def getStoreMenusPaginated(storeId, page: int = 1, limit: int = PER_PAGE):
  json_data = []
  menus = getStoreMenus(storeId)

  menus_list = []
  if menus != None:
    for menu in menus:
      menus_list.append(formatMenu(menu))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(menus) / limit)
  total_rows = len(menus)
  
  # Get paged data
  json_data = menus_list[start:end]

  return (json_data, total_rows, total_pages)