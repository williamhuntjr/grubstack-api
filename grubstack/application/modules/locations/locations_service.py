from pypika import PostgreSQLQuery, Query, Table, Tables, Order, functions, Parameter

from grubstack import app, gsdb, gsprod

from grubstack.application.modules.products.menus.menus_utilities import format_menu
from grubstack.application.modules.restaurant.restaurant_utilities import format_order_type
from grubstack.application.utilities.filters import generate_paginated_data

from .locations_utilities import format_location, format_work_hour, format_property, format_work_hour_params
from .locations_constants import PER_PAGE, DEFAULT_FILTERS, DEFAULT_LOCATION_LIMIT

def format_item(item: dict, ingredients_list = [], varieties_list: list = []):
  json_data = {
    "id": item['item_id'],
    "name": item['name'],
    "description": item['description'],
    "thumbnail_url": item['thumbnail_url'],
    "ingredients": ingredients_list,
    "varieties": varieties_list
  }
  
  if 'price' in item and 'is_onsale' in item and 'sale_price' in item:
    json_data['price'] = item['price']
    json_data['is_onsale'] = item['is_onsale']
    json_data['sale_price'] = item['sale_price']

  return json_data

class LocationService:
  def __init__(self):
    pass

  def apply_filters(self, location: dict, filters: list = []):
    if len(filters) <= 0:
      filters = DEFAULT_FILTERS

    menus_list = []

    if 'showMenus' in filters and filters['showMenus']:
      menus = self.get_menus(location['location_id'])
      if menus != None:
        for menu in menus:
          items_list = []
          if 'showItems' in filters and filters['showItems']:
            items = self.get_menu_items(menu['menu_id'])

            for item in items:
              items_list.append(format_item(item))

          menus_list.append(format_menu(menu, items_list, filters))

    return format_location(location, menus_list, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    if len(filters) <= 0:
      filters = DEFAULT_FILTERS

    gs_location = Table('gs_location')

    qry = Query.from_(
      gs_location
    ).select(
      '*'
    ).orderby(
      gs_location.create_date, order=Order.asc
    )
    
    if 'isActive' in filters:
      if isinstance(filters['isActive'], str):
        active_filter = 't' if filters['isActive'].lower() == 'true' else 'f'
      if isinstance(filters['isActive'], bool):
        active_filter = filters['isActive']

      qry = qry.where(gs_location.is_active == active_filter)
  
    locations = gsdb.fetchall(str(qry))

    filtered = []
    for location in locations:
      filtered.append(self.apply_filters(location, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def create(self, params: dict = ()):
    name, address1, city, state, postal, location_type, phone_number, is_active = params

    gs_location = Table('gs_location')
    qry = PostgreSQLQuery.into(
      gs_location
    ).columns(
      gs_location.tenant_id,
      gs_location.name,
      gs_location.address1,
      gs_location.city,
      gs_location.state,
      gs_location.postal,
      gs_location.location_type,
      gs_location.phone_number,
      gs_location.is_active
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s')
    ).returning('location_id')

    return gsdb.fetchone(str(qry), (name, address1, city, state, postal, location_type, phone_number, is_active,))

  def search(self, name: str, filters: list = []):
    if len(filters) <= 0:
      filters = DEFAULT_FILTERS

    gs_location = Table('gs_location')
    qry = Query.from_(
      gs_location
    ).select(
      '*'
    ).where(
      gs_location.name == name
    )

    location = gsdb.fetchone(str(qry))

    if location is not None:
      filtered_data = self.apply_filters(location, filters)
      return filtered_data

    else:
      return None

  def get(self, location_id: int, filters: list = []):
    if len(filters) <= 0:
      filters = DEFAULT_FILTERS

    gs_location = Table('gs_location')
    qry = Query.from_(
      gs_location
    ).select(
      '*'
    ).where(
      gs_location.location_id == location_id
    )

    location = gsdb.fetchone(str(qry))

    if location is not None:
      filtered_data = self.apply_filters(location, filters)
      return filtered_data

    else:
      return None

  def delete(self, location_id: int):
    gs_location = Table('gs_location')
    qry = Query.from_(
      gs_location
    ).delete().where(
      gs_location.location_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (location_id,))

    gs_location_employee = Table('gs_location_employee')
    qry = Query.from_(
      gs_location_employee
    ).delete().where(
      gs_location_employee.location_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (location_id,))

    gs_location_menu = Table('gs_location_menu')
    qry = Query.from_(
      gs_location_menu
    ).delete().where(
      gs_location_menu.location_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (location_id,))

    gs_location_order_type = Table('gs_location_order_type')
    qry = Query.from_(
      gs_location_order_type
    ).delete().where(
      gs_location_order_type.location_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (location_id,))

    gs_location_working_hour = Table('gs_location_working_hour')
    qry = Query.from_(
      gs_location_working_hour
    ).delete().where(
      gs_location_working_hour.location_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (location_id,))

  def update(self, location_id: int, params: dict = ()):
    name, address1, city, state, postal, location_type, phone_number, is_active = params

    gs_location = Table('gs_location')
    qry = Query.update(
      gs_location
    ).set(
      gs_location.name, Parameter('%s')
    ).set(
      gs_location.address1, Parameter('%s')
    ).set(
      gs_location.city, Parameter('%s')
    ).set(
      gs_location.state, Parameter('%s')
    ).set(
      gs_location.postal, Parameter('%s')
    ).set(
      gs_location.location_type, Parameter('%s')
    ).set(
      gs_location.phone_number, Parameter('%s')
    ).set(
      gs_location.is_active, Parameter('%s')
    ).where(
      gs_location.location_id == Parameter('%s')
    )

    return gsdb.execute(str(qry), (name, address1, city, state, postal, location_type, phone_number, is_active, location_id,))

  def get_menus(self, location_id: int):
    gs_menu, gs_location_menu = Tables('gs_menu', 'gs_location_menu')
    qry = Query.from_(
      gs_location_menu
    ).inner_join(
      gs_menu
    ).on(
      gs_menu.menu_id == gs_location_menu.menu_id
    ).select(
      gs_location_menu.menu_id,
      gs_menu.name,
      gs_menu.description,
      gs_menu.thumbnail_url
    ).where(
      gs_location_menu.location_id == Parameter('%s')
    ).orderby(
      gs_menu.name, order=Order.asc
    )

    return gsdb.fetchall(str(qry), (location_id,))

  def get_menus_paginated(self, store_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    menus = self.get_menus(store_id)

    menus_list = []
    items_list = []
    if menus != None:
      for menu in menus:
        items = self.get_menu_items(menu['menu_id'])

        for item in items:
          items_list.append(format_item(item))

        menus_list.append(format_menu(menu, items_list, {"showItems": True}))

    json_data, total_rows, total_pages = generate_paginated_data(menus_list, page, limit)

    return (json_data, total_rows, total_pages)

  def menu_exists(self, location_id: int, menu_id: int):
    gs_location_menu = Table('gs_location_menu')
    qry = Query.from_(
      gs_location_menu
    ).select(
      '*'
    ).where(
      gs_location_menu.location_id == location_id
    ).where(
      gs_location_menu.menu_id == menu_id
    )
    
    store = gsdb.fetchone(str(qry))

    if store is not None:
      return True
    
    return False

  def add_menu(self, location_id: int, menu_id: int):
    gs_location_menu = Table('gs_location_menu')
    qry = Query.into(
      gs_location_menu
    ).columns(
      gs_location_menu.tenant_id,
      gs_location_menu.location_id,
      gs_location_menu.menu_id
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s')
    )

    gsdb.execute(str(qry), (location_id, menu_id,))

  def delete_menu(self, location_id: int, menu_id: int):
    gs_location_menu = Table('gs_location_menu')
    qry = Query.from_(
      gs_location_menu
    ).delete().where(
      gs_location_menu.location_id == Parameter('%s')
    ).where(
      gs_location_menu.menu_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (location_id, menu_id,))

  def get_menu_items(self, menu_id: int):
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
      gs_item.thumbnail_url
    ).where(
      gs_menu_item.menu_id == Parameter('%s')
    ).orderby(
      gs_item.name, order=Order.asc
    )
    items = gsdb.fetchall(str(qry), (menu_id,))

    return items

  def get_location_count(self):
    gs_location = Table('gs_location')
    qry = Query.from_(
      gs_location
    ).select(
      functions.Count('*')
    )

    result = gsdb.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return 0

  def get_location_limit(self):
    gs_tenant_feature = Table('gs_tenant_feature')
    qry = Query.from_(
      gs_tenant_feature
    ).select(
      gs_tenant_feature.location_count
    ).where(
      gs_tenant_feature.tenant_id == app.config['TENANT_ID']
    )
    
    result = gsprod.fetchone(str(qry))

    if result != None:
      return result[0]
    
    return DEFAULT_LOCATION_LIMIT

  def get_order_types(self, location_id: int):
    gs_order_type, gs_location_order_type = Tables('gs_order_type', 'gs_location_order_type')
    qry = Query.from_(
      gs_location_order_type
    ).inner_join(
      gs_order_type
    ).on(
      gs_order_type.order_type_id == gs_location_order_type.order_type_id
    ).select(
      gs_location_order_type.order_type_id,
      gs_order_type.name,
      gs_order_type.description,
    ).where(
      gs_location_order_type.location_id == Parameter('%s')
    ).orderby(
      gs_order_type.name, order=Order.asc
    )

    order_types = gsdb.fetchall(str(qry), (location_id,))

    order_types_list = []
    for order_type in order_types:
      order_types_list.append(format_order_type(order_type))
    
    return order_types_list

  def order_type_exists(self, location_id: int, order_type_id: int):
    gs_location_order_type = Table('gs_location_order_type')
    qry = Query.from_(
      gs_location_order_type
    ).select(
      '*'
    ).where(
      gs_location_order_type.location_id == location_id
    ).where(
      gs_location_order_type.order_type_id == order_type_id
    )
  
    order_type = gsdb.fetchone(str(qry))

    if order_type is not None:
      return True
    
    return False

  def delete_order_type(self, location_id: int, order_type_id: int):
    gs_location_order_type = Table('gs_location_order_type')
    qry = Query.from_(
      gs_location_order_type
    ).delete().where(
      gs_location_order_type.location_id == Parameter('%s')
    ).where(
      gs_location_order_type.order_type_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (location_id, order_type_id,))

  def add_order_type(self, location_id: int, order_type_id: int):
    gs_location_order_type = Table('gs_location_order_type')
    qry = Query.into(
      gs_location_order_type
    ).columns(
      gs_location_order_type.tenant_id,
      gs_location_order_type.location_id,
      gs_location_order_type.order_type_id
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s')
    )

    gsdb.execute(str(qry), (location_id, order_type_id,))
  
  def initialize_work_hours(self, location_id: int):
    gs_working_hour_type = Table('gs_working_hour_type')

    qry = Query.from_(
      gs_working_hour_type
    ).select(
      '*'
    )

    working_hour_types = gsdb.fetchall(str(qry))

    for working_hour_type in working_hour_types:
      days = [0, 1, 2, 3, 4, 5, 6]

      for day in days: 
        params = {
          'day': day,
          'open_hour': 8,
          'open_minute': 0,
          'close_hour': 17,
          'close_minute': 0,
          'is_open': False
        }
        
        self.update_work_hour(location_id, working_hour_type['working_hour_type_id'], format_work_hour_params(params))

  def update_work_hour(self, location_id: int, working_hour_type_id: int, params: dict = ()):  
    day, open_hour, open_minute, close_hour, close_minute, is_open = params

    gs_location_working_hour = Table('gs_location_working_hour')

    qry = Query.from_(
      gs_location_working_hour
    ).select(
      '*'
    ).where(
      gs_location_working_hour.location_id == Parameter('%s')
    ).where(
      gs_location_working_hour.day == Parameter('%s')
    ).where(
      gs_location_working_hour.working_hour_type_id == Parameter('%s')
    )

    working_hour = gsdb.fetchone(str(qry), (location_id, day, working_hour_type_id,))

    if working_hour is not None:
      qry = Query.update(
        gs_location_working_hour
      ).set(
        gs_location_working_hour.open_hour, Parameter('%s')
      ).set(
        gs_location_working_hour.open_minute, Parameter('%s')
      ).set(
        gs_location_working_hour.close_hour, Parameter('%s')
      ).set(
        gs_location_working_hour.close_minute, Parameter('%s')
      ).set(
        gs_location_working_hour.is_open, Parameter('%s')
      ).where(
        gs_location_working_hour.location_id == Parameter('%s')
      ).where(
        gs_location_working_hour.day == Parameter('%s')
      ).where(
        gs_location_working_hour.working_hour_type_id == Parameter('%s')
      )

      gsdb.execute(str(qry), (open_hour, open_minute, close_hour, close_minute, is_open, location_id, day, working_hour_type_id,))

    else:
      qry = Query.into(
        gs_location_working_hour
      ).columns(
        gs_location_working_hour.tenant_id,
        gs_location_working_hour.location_id,
        gs_location_working_hour.day,
        gs_location_working_hour.open_hour,
        gs_location_working_hour.open_minute,
        gs_location_working_hour.close_hour,
        gs_location_working_hour.close_minute,
        gs_location_working_hour.is_open,
        gs_location_working_hour.working_hour_type_id
      ).insert(
        app.config['TENANT_ID'],
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s')
      )

      gsdb.execute(str(qry), (location_id, day, open_hour, open_minute, close_hour, close_minute, is_open, working_hour_type_id,))
  
  def get_work_hours(self, location_id: int):
    gs_location_working_hour = Table('gs_location_working_hour')

    qry = Query.from_(
      gs_location_working_hour
    ).select(
      '*'
    ).where(
      gs_location_working_hour.location_id == Parameter('%s')
    ).orderby(
      gs_location_working_hour.day, order=Order.asc
    )
    
    work_hours = gsdb.fetchall(str(qry), (location_id,))

    work_hours_list = []
    for work_hour in work_hours:
      work_hours_list.append(format_work_hour(work_hour))
    
    return work_hours_list

  def get_all_properties(self, location_id: int):
    gs_location_property = Table('gs_location_property')

    qry = Query.from_(
      gs_location_property
    ).select(
      '*'
    ).where(
      gs_location_property.location_id == Parameter('%s')
    ).orderby(
      gs_location_property.key, order=Order.asc
    )

    properties = gsdb.fetchall(str(qry), (location_id,))

    properties_list = []
    for location_property in properties:
      properties_list.append(format_property(location_property))
  
    return properties_list

  def property_exists(self, location_id: int, key: str):
    gs_location_property = Table('gs_location_property')
    qry = Query.from_(
      gs_location_property
    ).select(
      '*'
    ).where(
      gs_location_property.location_id == Parameter('%s')
    ).where(
      gs_location_property.key == Parameter('%s')
    )
    
    location_property = gsdb.fetchone(str(qry), (location_id, key,))

    if location_property is not None:
      return True
    
    return False

  def get_property(self, location_id: int, key: str):
    gs_location_property = Table('gs_location_property')
    qry = Query.from_(
      gs_location_property
    ).select(
      '*'
    ).where(
      gs_location_property.location_id == Parameter('%s')
    ).where(
      gs_location_property.key == Parameter('%s')
    )
    
    location_property = gsdb.fetchone(str(qry), (location_id, key,))

    return format_property(location_property)

  def update_property(self, location_id: int, key: str, value: str):
    gs_location_property = Table('gs_location_property')

    if self.property_exists(location_id, key):
      qry = Query.update(
        gs_location_property
      ).set(
        gs_location_property.value, Parameter('%s')
      ).where(
        gs_location_property.key == Parameter('%s')
      ).where(
        gs_location_property.location_id == Parameter('%s')
      )

      return gsdb.execute(str(qry), (value, key, location_id,))

    else:
      qry = Query.into(
        gs_location_property
      ).columns(
        gs_location_property.tenant_id,
        gs_location_property.location_id,
        gs_location_property.key,
        gs_location_property.value,
      ).insert(
        app.config['TENANT_ID'],
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
      )

      return gsdb.execute(str(qry), (location_id, key, value,))