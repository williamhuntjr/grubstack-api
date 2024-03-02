from pypika import Query, Table, Order, functions, Parameter, Tables

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
            menus = self.get_store_menus(store['store_id'])

            for menu in menus:
              menus_list.append(format_menu(menu))

          stores_list.append(format_store(store, menus_list, filters))

    return format_franchise(franchise, stores_list, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    gs_franchise = Table('gs_franchise')
    qry = Query.from_(
      gs_franchise
    ).select(
      '*'
    ).orderby(
      gs_franchise.name,
      order=Order.asc
    )
    
    franchises = gsdb.fetchall(str(qry))

    filtered = []
    for franchise in franchises:
      filtered.append(self.apply_filters(franchise, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, franchise_id: int, filters: list = []):
    stores_list = []

    gs_franchise = Table('gs_franchise')
    qry = Query.from_(
      gs_franchise
    ).select(
      '*'
    ).where(
      gs_franchise.franchise_id == franchise_id
    )

    franchise = gsdb.fetchone(str(qry))

    filtered_data = self.apply_filters(franchise, filters)

    return filtered_data

  def search(self, franchise_name: str):
    gs_franchise = Table('gs_franchise')
    qry = Query.from_(
      gs_franchise
    ).select(
      '*'
    ).where(
      gs_franchise.name == franchise_name
    )
    
    franchise = gsdb.fetchone(str(qry))

    if franchise != None:
      return format_franchise(franchise)

    return None

  def create(self, params: tuple = ()):
    name, description, thumbnail_url = params

    gs_franchise = Table('gs_franchise')
    qry = Query.into(
      gs_franchise
    ).columns(
      gs_franchise.tenant_id,
      gs_franchise.name,
      gs_franchise.description,
      gs_franchise.thumbnail_url
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
    )
    
    return gsdb.execute(str(qry), (name, description, thumbnail_url))

  def update(self, franchise_id: int, params: tuple = ()):
    name, description, thumbnail_url = params

    gs_franchise = Table('gs_franchise')
    qry = Query.update(
      gs_franchise
    ).set(
      gs_franchise.name, Parameter('%s')
    ).set(
      gs_franchise.description, Parameter('%s')
    ).set(
      gs_franchise.thumbnail_url, Parameter('%s')
    ).where(
      gs_franchise.franchise_id == Parameter('%s')
    )

    return gsdb.execute(str(qry), (name, description, thumbnail_url, franchise_id))

  def delete(self, franchise_id: int):
    gs_franchise, gs_franchise_store = Tables('gs_franchise', 'gs_franchise_store')
    qry = Query.from_(
      gs_franchise
    ).delete().where(
      gs_franchise.franchise_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (franchise_id))

    qry = Query.from_(
      gs_franchise_store
    ).delete().where(
      gs_franchise_store.franchise_id == Parameter('%s')
    )
    
    gsdb.execute(str(qry), (franchise_id))

  def get_stores(self, franchise_id: int):
    gs_store, gs_franchise_store = Tables('gs_store', 'gs_franchise_store')
    qry = Query.from_(
      gs_franchise_store
    ).inner_join(
      gs_store
    ).on(
      gs_store.store_id == gs_franchise_store.store_id
    ).select(
      gs_franchise_store.store_id,
      gs_store.name,
      gs_store.address1,
      gs_store.city,
      gs_store.state,
      gs_store.postal,
      gs_store.store_type,
      gs_store.thumbnail_url,
      gs_store.phone_number
    ).where(
      gs_franchise_store.franchise_id == franchise_id
    ).orderby(
      gs_store.name, order=Order.asc
    )

    return gsdb.fetchall(str(qry))

  def get_store_menus(self, store_id: int):
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
      gs_store_menu.store_id == Parameter('%s')
    ).orderby(
      gs_menu.name, order=Order.asc
    )

    stores = gsdb.fetchall(str(qry), (store_id,))

    return stores

  def add_store(self, franchise_id: int, store_id: int):
    gs_franchise_store = Table('gs_franchise_store')
    qry = Query.into(
      gs_franchise_store
    ).columns(
      gs_franchise_store.tenant_id,
      gs_franchise_store.franchise_id,
      gs_franchise_store.store_id,
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s')
    )

    return gsdb.execute(str(qry), (franchise_id, store_id))

  def delete_store(self, franchise_id: int, store_id: int):
    gs_franchise_store = Table('gs_franchise_store')
    qry = Query.from_(
      gs_franchise_store
    ).delete().where(
      gs_franchise_store.franchise_id == Parameter('%s')
    ).where(
      gs_franchise_store.store_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (franchise_id, store_id))

  def store_exists(self, franchise_id: int, store_id: int):
    gs_franchise_store = Table('gs_franchise_store')
    qry = Query.from_(
      gs_franchise_store
    ).select(
      '*'
    ).where(
      gs_franchise_store.franchise_id == franchise_id
    ).where(
      gs_franchise_store.store_id == store_id
    )
    
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
    gs_franchise = Table('gs_franchise')
    qry = Query.from_(
      gs_franchise
    ).select(
      functions.Count('*')
    )
    result = gsdb.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return 0

  def get_franchise_limit(self):
    gs_tenant_feature = Table('gs_tenant_feature')
    qry = Query.from_(
      gs_tenant_feature
    ).select(
      gs_tenant_feature.franchise_count
    ).where(
      gs_tenant_feature.tenant_id == app.config['TENANT_ID']
    )
    
    result = gsprod.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return DEFAULT_FRANCHISE_LIMIT