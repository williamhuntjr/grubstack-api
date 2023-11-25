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

    if 'showStores' in filters and filters['showStores']:
      items = self.get_items(menu['menu_id'])

      if items != None:
        for item in items:
          menus_list = []
          items_list.append(formatItem(item, menus_list, filters))

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

  def get_items(self, menu_id: int):
    return gsdb.fetchall("""SELECT c.item_id, name, address1, city, state, postal, item_type, thumbnail_url, phone_number
                              FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                              WHERE p.menu_id = %s ORDER BY name ASC""", (menu_id,))

  def get_items_paginated(self, menu_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    items = self.get_items(menu_id)

    items_list = []
    if items != None:
      for item in items:
        items_list.append(formatItem(item))

    json_data, total_rows, total_pages = generate_paginated_data(items_list, page, limit)

    return (json_data, total_rows, total_pages)