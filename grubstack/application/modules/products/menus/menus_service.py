from math import ceil
from pypika import PostgreSQLQuery, Query, Table, Tables, Order, functions, Parameter

from grubstack import app, gsdb, gsprod
from grubstack.application.modules.products.items.items_utilities import format_item
from grubstack.application.utilities.filters import generate_paginated_data

from .menus_utilities import format_menu
from .menus_constants import PER_PAGE, DEFAULT_FILTERS

class MenuService:
  def __init__(self):
    pass

  def apply_filters(self, menu, filters: list = []):
    items_list = []

    if 'showItems' in filters and filters['showItems']:
      items = self.get_items(menu['menu_id'])
      if items != None:
        for item in items:
          items_list.append(format_item(item, [], [], filters))

    return format_menu(menu, items_list, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    if len(filters) <= 0:
      filters = DEFAULT_FILTERS

    gs_menu = Table('gs_menu')

    qry = Query.from_(
      gs_menu
    ).select(
      '*'
    ).orderby(
      gs_menu.name, order=Order.asc
    ) 

    menus = gsdb.fetchall(str(qry))

    filtered = []

    for menu in menus:
      filtered.append(self.apply_filters(menu, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, menu_id: int, filters: list = []):
    gs_menu = Table('gs_menu')
    qry = Query.from_(
      gs_menu
    ).select(
      '*'
    ).where(
      gs_menu.menu_id == menu_id
    )

    menu = gsdb.fetchone(str(qry))

    if menu is not None:
      filtered_data = self.apply_filters(menu, filters)
      return filtered_data

    else:
      return None

  def search(self, name: str, filters: list = []):
    gs_menu = Table('gs_menu')
    qry = Query.from_(
      gs_menu
    ).select(
      '*'
    ).where(
      gs_menu.name == Parameter('%s')
    )

    menu = gsdb.fetchone(str(qry), (name,))

    if menu is not None:
      filtered_data = self.apply_filters(menu, filters)
      return filtered_data

    else:
      return None

  def get_by_slug(self, slug: str, filters: list = []):
    gs_menu = Table('gs_menu')
    qry = Query.from_(
      gs_menu
    ).select(
      '*'
    ).where(
      gs_menu.slug == Parameter('%s')
    )

    menu = gsdb.fetchone(str(qry), (slug,))

    if menu is not None:
      filtered_data = self.apply_filters(menu, filters)
      return filtered_data

    else:
      return None

  def create(self, params: dict = ()):
    name, description, thumbnail_url, slug = params

    gs_menu = Table('gs_menu')
    qry = PostgreSQLQuery.into(
      gs_menu
    ).columns(
      gs_menu.tenant_id,
      gs_menu.name,
      gs_menu.description,
      gs_menu.thumbnail_url,
      gs_menu.slug
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s')
    ).returning('menu_id')

    return gsdb.fetchone(str(qry), (name, description, thumbnail_url, slug,))

  def update(self, menu_id: int, params: dict = ()):
    name, description, thumbnail_url, slug = params

    gs_menu = Table('gs_menu')
    qry = Query.update(
      gs_menu
    ).set(
      gs_menu.name, Parameter('%s')
    ).set(
      gs_menu.description, Parameter('%s')
    ).set(
      gs_menu.thumbnail_url, Parameter('%s')
    ).set(
      gs_menu.slug, Parameter('%s')
    ).where(
      gs_menu.menu_id == Parameter('%s')
    )

    return gsdb.execute(str(qry), (name, description, thumbnail_url, slug, menu_id,))

  def delete(self, menu_id: int):
    gs_menu = Table('gs_menu')
    qry = Query.from_(
      gs_menu
    ).delete().where(
      gs_menu.menu_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (menu_id,))

    gs_menu_item = Table('gs_menu_item')
    qry = Query.from_(
      gs_menu_item
    ).delete().where(
      gs_menu_item.menu_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (menu_id,))

  def get_items(self, menu_id: int):
    gs_item, gs_menu_item = Tables('gs_item', 'gs_menu_item')
    qry = Query.from_(
      gs_menu_item
    ).inner_join(
      gs_item
    ).on(
      gs_item.item_id == gs_menu_item.item_id
    ).select(
      gs_menu_item.item_id,
      gs_item.name,
      gs_item.description,
      gs_item.thumbnail_url,
      gs_item.slug,
      gs_menu_item.price,
      gs_menu_item.sale_price,
      gs_menu_item.is_onsale
    ).where(
      gs_menu_item.menu_id == Parameter('%s')
    ).orderby(
      gs_item.name, order=Order.asc
    )

    return gsdb.fetchall(str(qry), (menu_id,))

  def add_item(self, menu_id: int, item_id: int, params: dict):
    gs_menu_item = Table('gs_menu_item')
    qry = Query.into(
      gs_menu_item
    ).columns(
      gs_menu_item.tenant_id,
      gs_menu_item.menu_id,
      gs_menu_item.item_id,
      gs_menu_item.price,
      gs_menu_item.sale_price,
      gs_menu_item.is_onsale,
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      0,
      0,
      'f'
    )

    gsdb.execute(str(qry), (menu_id, item_id,))

  def delete_item(self, menu_id: int, item_id: int):
    gs_menu_item = Table('gs_menu_item')
    qry = Query.from_(
      gs_menu_item
    ).delete().where(
      gs_menu_item.menu_id == Parameter('%s')
    ).where(
      gs_menu_item.item_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (menu_id, item_id,))

  def update_item(self, menu_id: int, item_id: int, params: dict):
    price, sale_price, is_onsale = params

    gs_menu_item = Table('gs_menu_item')
    qry = Query.update(
      gs_menu_item
    ).set(
      gs_menu_item.price, Parameter('%s')
    ).set(
      gs_menu_item.sale_price, Parameter('%s')
    ).set(
      gs_menu_item.is_onsale, Parameter('%s')
    ).where(
      gs_menu_item.menu_id == Parameter('%s')
    ).where(
      gs_menu_item.item_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (price, sale_price, is_onsale, menu_id, item_id,))

  def item_exists(self, menu_id: int, item_id: int):
    gs_menu_item = Table('gs_menu_item')
    qry = Query.from_(
      gs_menu_item
    ).select(
      '*'
    ).where(
      gs_menu_item.menu_id == menu_id
    ).where(
      gs_menu_item.item_id == item_id
    )
    
    item = gsdb.fetchone(str(qry))

    if item is not None:
      return True
    
    return False

  def get_items_paginated(self, menu_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    items = self.get_items(menu_id)

    items_list = []
    if items != None:
      for item in items:
        items_list.append(format_item(item))

    json_data, total_rows, total_pages = generate_paginated_data(items_list, page, limit)

    return (json_data, total_rows, total_pages)

  def get_menu_item(self, menu_id: int, item_id: int):
    gs_menu_item = Table('gs_menu_item')
    qry = Query.from_(
      gs_menu_item
    ).select(
      '*'
    ).where(
      gs_menu_item.menu_id == Parameter('%s')
    ).where(
      gs_menu_item.item_id == Parameter('%s')
    )

    return gsdb.fetchone(str(qry), (menu_id, item_id,))
