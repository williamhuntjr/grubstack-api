from math import ceil
from pypika import Query, Table, Order, functions

from grubstack import app, gsdb, gsprod
from grubstack.application.modules.stores.stores_utilities import format_store
from grubstack.application.modules.products.menus.menus_utilities import format_menu
from grubstack.application.constants import DEFAULT_FRANCHISE_LIMIT
from grubstack.application.utilities.filters import generate_paginated_data

from .franchises_utilities import format_franchise
from .franchises_constants import PER_PAGE

class FranchiseService:
  def __init__(self):
    pass

  def apply_filters(self, franchise, filters: list = []):
    stores_list = []

    if 'showStores' in filters and filters['showStores']:
      stores = self.get_stores(franchise['franchise_id'])

      if stores != None:
        for store in stores:
          menus_list = []

          if 'showMenus' in filters and filters['showMenus']:
            menus = gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url, label_color
                                    FROM gs_menu c INNER JOIN gs_store_menu p ON p.menu_id = c.menu_id 
                                    WHERE p.store_id = %s ORDER BY name ASC""", (store['store_id'],))

            for menu in menus:
              menus_list.append(format_menu(menu))

          stores_list.append(format_store(store, menus_list, filters))

    return format_franchise(franchise, stores_list, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    qry = Query.from_('gs_franchise').select('*').orderby('name', order=Order.asc)
    franchises = gsdb.fetchall(str(qry),)

    filtered = []
    for franchise in franchises:
      filtered.append(self.apply_filters(franchise, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, franchise_id: int, filters: list = []):
    stores_list = []

    table = Table('gs_franchise')
    qry = Query.from_('gs_franchise').select('*').where(table.franchise_id == franchise_id)

    franchise = gsdb.fetchone(str(qry))
    filtered_data = self.apply_filters(franchise, filters)
    return filtered_data

  def search(self, franchise_name: str):
    table = Table('gs_franchise')
    qry = Query.from_('gs_franchise').select('*').where(table.name == franchise_name)
    
    franchise = gsdb.fetchone(str(qry))

    if franchise != None:
      return format_franchise(franchise)

    return

  def create(self, params: tuple = ()):
    name, description, thumbnail_url = params
    return gsdb.execute("""INSERT INTO gs_franchise 
                      (tenant_id, franchise_id, name, description, thumbnail_url) 
                      VALUES 
                      (%s, DEFAULT, %s, %s, %s)""", (app.config["TENANT_ID"], name, description, thumbnail_url))

  def update(self, franchise_id: int, params: tuple = ()):
    name, description, thumbnail_url = params
    return gsdb.execute("UPDATE gs_franchise SET (name, description, thumbnail_url) = (%s, %s, %s) WHERE franchise_id = %s", (name, description, thumbnail_url, franchise_id,))

  def delete(self, franchise_id: int):
    gsdb.execute("DELETE FROM gs_franchise WHERE franchise_id = %s", (franchise_id,))
    gsdb.execute("DELETE FROM gs_franchise_store WHERE franchise_id = %s", (franchise_id,))

  def exists(self, franchise_name: str):
    table = Table('gs_franchise')
    qry = Query.from_('gs_franchise').select('*').where(table.name == franchise_name)
    
    franchises = gsdb.fetchall(str(qry))

    if len(franchises) > 0:
      return True
    
    return False

  def get_stores(self, franchise_id: int):
    return gsdb.fetchall("""SELECT c.store_id, name, address1, city, state, postal, store_type, thumbnail_url, phone_number
                              FROM gs_store c INNER JOIN gs_franchise_store p ON p.store_id = c.store_id 
                              WHERE p.franchise_id = %s ORDER BY name ASC""", (franchise_id,))

  def add_store(self, franchise_id: int, store_id: int):
    return gsdb.execute("""INSERT INTO gs_franchise_store 
                            (tenant_id, franchise_id, store_id)
                            VALUES 
                            (%s, %s, %s)""", (app.config["TENANT_ID"], franchise_id, store_id,))

  def delete_store(self, franchise_id: int, store_id: int):
    gsdb.execute("DELETE FROM gs_franchise_store WHERE franchise_id = %s AND store_id = %s", (franchise_id, store_id,))

  def store_exists(self, franchise_id: int, store_id: int):
    table = Table('gs_franchise_store')
    qry = Query.from_('gs_franchise_store').select('*').where(table.franchise_id == franchise_id).where(table.store_id == store_id)
    
    store = gsdb.fetchone(str(qry))

    if store is not None:
      return True
    
    return False

  def get_stores_paginated(self, franchise_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    stores_list = []

    stores = self.get_stores(franchise_id)
    
    if stores != None:
      for store in stores:
        stores_list.append(format_store(store))

    json_data, total_rows, total_pages = generate_paginated_data(stores_list, page, limit)

    return (json_data, total_rows, total_pages)
    
  def get_franchise_count(self):
    qry = Query.from_('gs_franchise').select(functions.Count('*'))
    result = gsdb.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return 0

  def get_franchise_limit(self):
    table = Table('gs_tenant_features')
    qry = Query.from_('gs_tenant_features').select('franchise_count').where(table.tenant_id == app.config['TENANT_ID'])
    
    result = gsprod.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return DEFAULT_FRANCHISE_LIMIT