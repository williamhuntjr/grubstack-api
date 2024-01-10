from math import ceil
from pypika import Query, Table, Order, functions

from grubstack import app, gsdb, gsprod
from grubstack.application.modules.products.menus.menus_utilities import format_menu
from grubstack.application.modules.products.items.items_utilities import formatItem
from grubstack.application.constants import DEFAULT_STORE_LIMIT
from grubstack.application.utilities.filters import generate_paginated_data

from .stores_utilities import format_store

from .stores_constants import PER_PAGE

class StoreService:
  def __init__(self):
    pass

  def apply_filters(self, store, filters: list = []):
    menus_list = []

    if 'showMenus' in filters and filters['showMenus']:
      menus = self.get_menus(store['store_id'])

      if menus != None:
        for menu in menus:
          items_list = []

          if 'showItems' in filters and filters['showItems']:
            items = gsdb.fetchall("""SELECT c.item_id, name, description, thumbnail_url, label_color, price, sale_price, is_onsale
                      FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                      WHERE p.menu_id = %s ORDER BY name ASC""", (menu['menu_id'],))
            
            for item in items:
              items_list.append(formatItem(item))

          menus_list.append(format_menu(menu, items_list, filters))

    return format_store(store, menus_list, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    qry = Query.from_('gs_store').select('*').orderby('name', order=Order.asc)
    stores = gsdb.fetchall(str(qry))

    filtered = []
    for store in stores:
      filtered.append(self.apply_filters(store, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, store_id: int, filters: list = []):
    table = Table('gs_store')
    qry = Query.from_('gs_store').select('*').where(table.store_id == store_id)

    store = gsdb.fetchone(str(qry))
    filtered_data = self.apply_filters(store, filters)
    return filtered_data

  def search(self, store_name: str, store_type: str):
    table = Table('gs_store')
    qry = Query.from_('gs_store').select('*').where(table.name == store_name).where(table.store_type == store_type)
    
    store = gsdb.fetchone(str(qry))
    if store:
      return format_store(store)
    
    return

  def create(self, params: dict = ()):
    name, address1, city, state, postal, store_type, thumbnail_url, phone_number = params
    return gsdb.execute("""INSERT INTO gs_store 
                      (tenant_id, store_id, name, address1, city, state, postal, store_type, thumbnail_url, phone_number) 
                      VALUES 
                      (%s, DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s)""", (app.config["TENANT_ID"], name, address1, city, state, postal, store_type, thumbnail_url, phone_number))

  def update(self, store_id: int, params: dict = ()):
    name, address1, city, state, postal, store_type, thumbnail_url, phone_number = params
    return gsdb.execute("UPDATE gs_store SET (name, address1, city, state, postal, store_type, thumbnail_url, phone_number) = (%s, %s, %s, %s, %s, %s, %s, %s) WHERE store_id = %s", (name, address1, city, state, postal, store_type, thumbnail_url, phone_number, store_id,))
  
  def delete(self, store_id: int):
    gsdb.execute("DELETE FROM gs_store WHERE store_id = %s", (store_id,))
    gsdb.execute("DELETE FROM gs_store_menu WHERE store_id = %s", (store_id,))

  def exists(self, store_name: str, store_type: str):
    table = Table('gs_store')
    qry = Query.from_('gs_store').select('*').where(table.name == store_name).where(table.store_type == store_type)
    
    stores = gsdb.fetchall(str(qry))

    if len(stores) > 0:
      return True
    
    return False

  def get_menus(self, store_id: int):
    return gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url, label_color
                                    FROM gs_menu c INNER JOIN gs_store_menu p ON p.menu_id = c.menu_id 
                                    WHERE p.store_id = %s ORDER BY name ASC""", (store_id,))

  def add_menu(self, store_id: int, menu_id: int):
    return gsdb.execute("""INSERT INTO gs_store_menu 
                                  (tenant_id, store_id, menu_id)
                                  VALUES 
                                  (%s, %s, %s)""", (app.config["TENANT_ID"], store_id, menu_id,))

  def delete_menu(self, store_id: int, menu_id: int):
    gsdb.execute("DELETE FROM gs_store_menu WHERE store_id = %s AND menu_id = %s", (store_id, menu_id,))

  def menu_exists(self, store_id: int, menu_id: int):
    table = Table('gs_store_menu')
    qry = Query.from_('gs_store_menu').select('*').where(table.store_id == store_id).where(table.menu_id == menu_id)
    
    store = gsdb.fetchone(str(qry))

    if store is not None:
      return True
    
    return False

  def get_menus_paginated(self, store_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    menus = self.get_menus(store_id)

    menus_list = []
    if menus != None:
      for menu in menus:
        menus_list.append(format_menu(menu))

    json_data, total_rows, total_pages = generate_paginated_data(menus_list, page, limit)

    return (json_data, total_rows, total_pages)
    
  def get_store_count(self):
    qry = Query.from_('gs_store').select(functions.Count('*'))
    result = gsdb.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return 0

  def get_store_limit(self):
    table = Table('gs_tenant_feature')
    qry = Query.from_('gs_tenant_feature').select('store_count').where(table.tenant_id == app.config['TENANT_ID'])
    
    result = gsprod.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return DEFAULT_STORE_LIMIT