from math import ceil
from pypika import Query, Table, Order, functions

from grubstack import app, gsdb, gsprod
from grubstack.application.modules.products.items.items_utilities import formatItem
from grubstack.application.utilities.filters import generate_paginated_data

from .menus_utilities import format_menu
from .menus_constants import PER_PAGE

class MenuService:
  def __init__(self):
    pass

  def apply_filters(self, menu, filters: list = []):
    items_list = []

    if 'showItems' in filters and filters['showItems']:
      items = self.get_items(menu['menu_id'])
      if items != None:
        for item in items:
          items_list.append(formatItem(item, [], [], filters))

    return format_menu(menu, items_list, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    qry = Query.from_('gs_menu').select('*').orderby('name', order=Order.asc)
    menus = gsdb.fetchall(str(qry),)

    filtered = []
    for menu in menus:
      filtered.append(self.apply_filters(menu, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, menu_id: int, filters: list = []):
    items_list = []

    table = Table('gs_menu')
    qry = Query.from_('gs_menu').select('*').where(table.menu_id == menu_id)

    menu = gsdb.fetchone(str(qry))
    filtered_data = self.apply_filters(menu, filters)
    return filtered_data

  def search(self, menu_name: str):
    table = Table('gs_menu')
    qry = Query.from_('gs_menu').select('*').where(table.name == menu_name)
    
    menu = gsdb.fetchone(str(qry))

    if menu != None:
      return format_menu(menu)

    return

  def update(self, menu_id: int, params: dict = ()):
    name, description, thumbnail_url, label_color = params
    return gsdb.execute("UPDATE gs_menu SET (name, description, thumbnail_url, label_color) = (%s, %s, %s, %s) WHERE menu_id = %s", (name, description, thumbnail_url, label_color, menu_id,))

  def create(self, params: dict = ()):
    name, description, thumbnail_url, label_color = params
    return gsdb.execute("""INSERT INTO gs_menu 
                        (tenant_id, menu_id, name, description, thumbnail_url, label_color)
                        VALUES
                        (%s, DEFAULT, %s, %s, %s, %s)""", (app.config['TENANT_ID'], name, description, thumbnail_url, label_color,))

  def delete(self, menu_id: int):
    gsdb.execute("DELETE FROM gs_menu WHERE menu_id = %s", (menu_id,))
    gsdb.execute("DELETE FROM gs_menu_item WHERE menu_id = %s", (menu_id,))

  def exists(self, menu_name: str):
    table = Table('gs_menu')
    qry = Query.from_('gs_menu').select('*').where(table.name == menu_name)
    
    menus = gsdb.fetchall(str(qry))

    if len(menus) > 0:
      return True
    
    return False

  def get_item(self, menu_id: int, item_id: int):
    item = gsdb.fetchone("""SELECT c.item_id, name, description, thumbnail_url, label_color, price, sale_price, is_onsale
                  FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                  WHERE p.menu_id = %s AND c.item_id = %s ORDER BY name ASC""", (menu_id, item_id,))
    if item:
      return formatItem(item)
    return None

  def get_items(self, menu_id: int):
    return gsdb.fetchall("""SELECT c.item_id, name, description, thumbnail_url, label_color, price, sale_price, is_onsale
                      FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                      WHERE p.menu_id = %s ORDER BY name ASC""", (menu_id,))

  def add_item(self, menu_id: int, item_id: int, params: dict):
    price, sale_price, is_onsale = params
    return gsdb.execute("""INSERT INTO gs_menu_item 
                                  (tenant_id, menu_id, item_id, price, sale_price, is_onsale)
                                  VALUES 
                                  (%s, %s, %s, %s, %s, %s)""", (app.config['TENANT_ID'], menu_id, item_id, price, sale_price, is_onsale,))

  def delete_item(self, menu_id: int, item_id: int):
    gsdb.execute("DELETE FROM gs_menu_item WHERE menu_id = %s AND item_id = %s", (menu_id, item_id,))

  def update_item(self, menu_id: int, item_id: int, params: dict):
    price, sale_price, is_onsale = params
    gsdb.execute("UPDATE gs_menu_item SET price = %s, sale_price = %s, is_onsale = %s WHERE menu_id = %s AND item_id = %s", (price, sale_price, is_onsale, menu_id, item_id,))
  
  def item_exists(self, menu_id: int, item_id: int):
    table = Table('gs_menu_item')
    qry = Query.from_('gs_menu_item').select('*').where(table.menu_id == menu_id).where(table.item_id == item_id)
    
    restaurant = gsdb.fetchone(str(qry))

    if restaurant is not None:
      return True
    
    return False

  def get_items_paginated(self, menu_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    items = self.get_items(menu_id)

    items_list = []
    if items != None:
      for item in items:
        items_list.append(formatItem(item))

    json_data, total_rows, total_pages = generate_paginated_data(items_list, page, limit)

    return (json_data, total_rows, total_pages)