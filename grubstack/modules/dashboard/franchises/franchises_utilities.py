from grubstack import app, gsdb
from math import ceil

PER_PAGE = app.config['PER_PAGE']

def formatFranchise(franchise: dict, stores_list: list):
  return {
    "id": franchise['franchise_id'],
    "name": franchise['name'],
    "description": franchise['description'],
    "thumbnail_url": franchise['thumbnail_url'],
    "stores": stores_list
  }

def formatParams(params: dict):
  name = params['name']
  description = params['description'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']

  return (name, description, thumbnail_url)

def getFranchises(page: int = 1, limit: int = PER_PAGE):
  json_data = []
  franchises = gsdb.fetchall("SELECT * FROM gs_franchise ORDER BY name ASC")
  
  franchises_list = []
  for franchise in franchises:
    stores = gsdb.fetchall("""SELECT c.store_id, name, address1, city, state, postal, store_type, thumbnail_url, phone_number
                              FROM gs_store c INNER JOIN gs_franchise_store p ON p.store_id = c.store_id 
                              WHERE p.franchise_id = %s ORDER BY name ASC""", (franchise['franchise_id'],))
    stores_list = []
    if stores != None:
      for store in stores:
        stores_list.append({
          "id": store['store_id'],
          "name": store['name'],
          "address1": store['address1'],
          "city": store['city'],
          "state": store['state'],
          "postal": store['postal'],
          "store_type": store['store_type'],
          "thumbnail_url": store['thumbnail_url'],
          "phone_number": store['phone_number'],
        })

    franchises_list.append(formatFranchise(franchise, stores_list))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(franchises) / limit)
  total_rows = len(franchises)

  json_data = franchises_list[start:end]
  return (json_data, total_rows, total_pages)

def getFranchiseStores(franchiseId, page: int = 1, limit: int = PER_PAGE):
  json_data = []
  stores = gsdb.fetchall("""SELECT c.store_id, name, address1, city, state, postal, store_type, thumbnail_url, phone_number
                            FROM gs_store c INNER JOIN gs_franchise_store p ON p.store_id = c.store_id 
                            WHERE p.franchise_id = %s ORDER BY name ASC""", (franchiseId,))

  stores_list = []
  if stores != None:
    for store in stores:
      stores_list.append({
        "id": store['store_id'],
        "name": store['name'],
        "address1": store['address1'],
        "city": store['city'],
        "state": store['state'],
        "postal": store['postal'],
        "store_type": store['store_type'],
        "thumbnail_url": store['thumbnail_url'],
        "phone_number": store['phone_number'],
      })

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(stores) / limit)
  total_rows = len(stores)
  
  # Get paged data
  json_data = stores_list[start:end]

  return (json_data, total_rows, total_pages)