from pypika import Query, Table, Tables, Order, functions, Parameter

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
            print("TEST")
            items = self.get_menu_items(menu['menu_id'])
            print(items)
            for item in items:
              items_list.append(formatItem(item))

          menus_list.append(format_menu(menu, items_list, filters))

    return format_store(store, menus_list, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    gs_store = Table('gs_store')
    qry = Query.from_(
      gs_store
    ).select(
      '*'
    ).orderby(
      gs_store.name, order=Order.asc
    )

    stores = gsdb.fetchall(str(qry))

    filtered = []
    for store in stores:
      filtered.append(self.apply_filters(store, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, store_id: int, filters: list = []):
    gs_store = Table('gs_store')
    qry = Query.from_(
      gs_store
    ).select(
      '*'
    ).where(
      gs_store.store_id == store_id
    )

    store = gsdb.fetchone(str(qry))

    if store is not None:
      filtered_data = self.apply_filters(store, filters)
      return filtered_data

    else:
      return None

  def search(self, store_name: str, store_type: str):
    gs_store = Table('gs_store')
    qry = Query.from_(
      gs_store
    ).select(
      '*'
    ).where(
      gs_store.name == store_name
    ).where(
      gs_store.store_type == store_type
    )
    
    store = gsdb.fetchone(str(qry))

    if store:
      return format_store(store)
    
    else:
      return None

  def create(self, params: dict = ()):
    name, address1, city, state, postal, store_type, thumbnail_url, phone_number = params

    gs_store = Table('gs_store')
    qry = Query.into(
      gs_store
    ).columns(
      gs_store.tenant_id,
      gs_store.name,
      gs_store.address1,
      gs_store.city,
      gs_store.state,
      gs_store.postal,
      gs_store.store_type,
      gs_store.thumbnail_url,
      gs_store.phone_number
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
    )

    return gsdb.execute(str(qry), (name, address1, city, state, postal, store_type, thumbnail_url, phone_number,))

  def update(self, store_id: int, params: dict = ()):
    name, address1, city, state, postal, store_type, thumbnail_url, phone_number = params

    gs_store = Table('gs_store')
    qry = Query.update(
      gs_store
    ).set(
      gs_store.name, Parameter('%s')
    ).set(
      gs_store.address1, Parameter('%s')
    ).set(
      gs_store.city, Parameter('%s')
    ).set(
      gs_store.state, Parameter('%s')
    ).set(
      gs_store.postal, Parameter('%s')
    ).set(
      gs_store.store_type, Parameter('%s')
    ).set(
      gs_store.thumbnail_url, Parameter('%s')
    ).set(
      gs_store.phone_number, Parameter('%s')
    ).where(
      gs_store.store_id == Parameter('%s')
    )

    return gsdb.execute(str(qry), (name, address1, city, state, postal, store_type, thumbnail_url, phone_number, store_id,))
  
  def delete(self, store_id: int):
    gs_store, gs_store_menu = Tables('gs_store', 'gs_store_menu')
    qry = Query.from_(
      gs_store
    ).delete().where(
      gs_store.store_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (store_id,))

    qry = Query.from_(
      gs_store_menu
    ).delete().where(
      gs_store_menu.store_id == Parameter('%s')
    )
    
    gsdb.execute(str(qry), (store_id,))

  def exists(self, store_name: str, store_type: str):
    gs_store = Table('gs_store')
    qry = Query.from_(
      gs_store
    ).select(
      '*'
    ).where(
      gs_store.name == store_name
    ).where(
      gs_store.store_type == store_type
    )
    
    stores = gsdb.fetchall(str(qry))

    if len(stores) > 0:
      return True
    
    return False

  def get_menus(self, store_id: int):
    gs_menu, gs_store_menu = Tables('gs_menu', 'gs_store_menu')
    qry = Query.from_(
      gs_store_menu
    ).inner_join(
      gs_menu
    ).on(
      gs_menu.menu_id == gs_store_menu.menu_id
    ).select(
      gs_store_menu.menu_id,
      gs_menu.name,
      gs_menu.description,
      gs_menu.thumbnail_url,
      gs_menu.label_color
    ).where(
      gs_store_menu.store_id == store_id
    ).orderby(
      gs_menu.name, order=Order.asc
    )

    return gsdb.fetchall(str(qry), (store_id,))

  def get_menu_items(self, menu_id: int):
    print("TEST2")
    gs_item, gs_menu_item = Tables('gs_item', 'gs_menu_item')
    qry = Query.from_(
      gs_menu_item
    ).inner_join(
      gs_item
    ).on(
      gs_item.item_id == gs_menu_item.item_id
    ).select(
      gs_menu_item.menu_id,
      gs_menu_item.item_id,
      gs_menu_item.price,
      gs_menu_item.sale_price,
      gs_menu_item.is_onsale,
      gs_item.name,
      gs_item.description,
      gs_item.thumbnail_url,
      gs_item.label_color,
    ).where(
      gs_menu_item.menu_id == Parameter('%s')
    ).orderby(
      gs_item.name, order=Order.asc
    )
    items = gsdb.fetchall(str(qry), (menu_id,))

    return items

  def add_menu(self, store_id: int, menu_id: int):
    gs_store_menu = Table('gs_store_menu')
    qry = Query.into(
      gs_store_menu
    ).columns(
      gs_store_menu.tenant_id,
      gs_store_menu.store_id,
      gs_store_menu.menu_id
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s')
    )

    gsdb.execute(str(qry), (store_id, menu_id,))

  def delete_menu(self, store_id: int, menu_id: int):
    gs_store_menu = Table('gs_store_menu')
    qry = Query.from_(
      gs_store_menu
    ).delete().where(
      gs_store_menu.store_id == Parameter('%s')
    ).where(
      gs_store_menu.menu_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (store_id, menu_id,))

  def menu_exists(self, store_id: int, menu_id: int):
    gs_store_menu = Table('gs_store_menu')
    qry = Query.from_(
      gs_store_menu
    ).select(
      '*'
    ).where(
      gs_store_menu.store_id == store_id
    ).where(
      gs_store_menu.menu_id == menu_id
    )
    
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
    gs_store = Table('gs_store')
    qry = Query.from_(
      gs_store
    ).select(
      functions.Count('*')
    )

    result = gsdb.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return 0

  def get_store_limit(self):
    gs_tenant_feature = Table('gs_tenant_feature')
    qry = Query.from_(
      gs_tenant_feature
    ).select(
      gs_tenant_feature.store_count
    ).where(
      gs_tenant_feature.tenant_id == app.config['TENANT_ID']
    )
    
    result = gsprod.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return DEFAULT_STORE_LIMIT