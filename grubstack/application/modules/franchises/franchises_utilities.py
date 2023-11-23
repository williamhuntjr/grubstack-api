from math import ceil

from grubstack import app, gsdb
from grubstack.application.modules.stores.stores_utilities import formatStore
from grubstack.application.modules.products.menus.menus_utilities import formatMenu
from grubstack.application.utilities.database import getFranchiseStores, getStoreMenus

PER_PAGE = app.config['PER_PAGE']

def formatFranchise(franchise: dict, stores_list: list, filters: list = []):
  json_data = {
    "id": franchise['franchise_id'],
    "name": franchise['name'],
    "description": franchise['description'],
    "thumbnail_url": franchise['thumbnail_url']
  }
  if 'showStores' in filters and filters['showStores']:
    json_data['stores'] = stores_list

  return json_data
  
def formatParams(params: dict):
  name = params['name']
  description = params['description'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']

  return (name, description, thumbnail_url)

def getFranchise(franchise_id: int, filters: list = []):
  json_data = []
  franchise = gsdb.fetchone("SELECT * FROM gs_franchise WHERE franchise_id = %s", (franchise_id,))
  stores_list = []

  if 'showStores' in filters and filters['showStores']:
    stores = getStores(franchise_id)

    if stores != None:
      for store in stores:
        menus_list = []

        if 'showMenus' in filters and filters['showMenus']:
          menus = getStoreMenus(store['store_id'])

          for menu in menus:
            menus_list.append(formatMenu(menu, []))
            
        stores_list.append(formatStore(store, menus_list, filters))
      
  return formatFranchise(franchise, stores_list, filters)

def getFranchises(page: int = 1, limit: int = PER_PAGE, filters: list = []):
  json_data = []
  franchises = gsdb.fetchall("SELECT * FROM gs_franchise ORDER BY name ASC")
  
  franchises_list = []
  for franchise in franchises:
    stores_list = []

    if 'showStores' in filters and filters['showStores']:
      stores = getFranchiseStores(franchise['franchise_id'])

      if stores != None:
        for store in stores:
          menus_list = []

          if 'showMenus' in filters and filters['showMenus']:
            menus = getStoreMenus(store['store_id'])
            for menu in menus:
              menus_list.append(formatMenu(menu, []))

          stores_list.append(formatStore(store, menus_list, filters))

    franchises_list.append(formatFranchise(franchise, stores_list, filters))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(franchises) / limit)
  total_rows = len(franchises)

  json_data = franchises_list[start:end]

  return (json_data, total_rows, total_pages)

def getFranchiseStoresPaginated(franchiseId, page: int = 1, limit: int = PER_PAGE):
  json_data = []
  stores = getFranchiseStores(franchiseId)

  stores_list = []
  if stores != None:
    for store in stores:
      stores_list.append(formatStore(store))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(stores) / limit)
  total_rows = len(stores)
  
  # Get paged data
  json_data = stores_list[start:end]

  return (json_data, total_rows, total_pages)