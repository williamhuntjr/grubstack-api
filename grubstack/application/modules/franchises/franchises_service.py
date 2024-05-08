from pypika import Query, Table, Order, functions, Parameter, Tables

from grubstack import app, gsdb, gsprod
from grubstack.application.modules.restaurants.restaurants_utilities import format_restaurant
from grubstack.application.modules.products.menus.menus_utilities import format_menu
from grubstack.application.constants import DEFAULT_FRANCHISE_LIMIT
from grubstack.application.utilities.filters import generate_paginated_data

from .franchises_utilities import format_franchise
from .franchises_constants import PER_PAGE

class FranchiseService:
  def __init__(self):
    pass

  def apply_filters(self, franchise, filters: list = []):
    restaurants_list = []

    if 'showRestaurants' in filters and filters['showRestaurants']:
      restaurants = self.get_restaurants(franchise['franchise_id'])

      if restaurants != None:
        for restaurant in restaurants:
          menus_list = []

          if 'showMenus' in filters and filters['showMenus']:
            menus = self.get_restaurant_menus(restaurant['restaurant_id'])

            for menu in menus:
              menus_list.append(format_menu(menu))

          restaurants_list.append(format_restaurant(restaurant, menus_list, filters))

    return format_franchise(franchise, restaurants_list, filters)

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
    restaurants_list = []

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
    
    return gsdb.execute(str(qry), (name, description, thumbnail_url,))

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

    return gsdb.execute(str(qry), (name, description, thumbnail_url, franchise_id,))

  def delete(self, franchise_id: int):
    gs_franchise, gs_franchise_restaurant = Tables('gs_franchise', 'gs_franchise_restaurant')
    qry = Query.from_(
      gs_franchise
    ).delete().where(
      gs_franchise.franchise_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (franchise_id,))

    qry = Query.from_(
      gs_franchise_restaurant
    ).delete().where(
      gs_franchise_restaurant.franchise_id == Parameter('%s')
    )
    
    gsdb.execute(str(qry), (franchise_id,))

  def get_restaurants(self, franchise_id: int):
    gs_restaurant, gs_franchise_restaurant = Tables('gs_restaurant', 'gs_franchise_restaurant')
    qry = Query.from_(
      gs_franchise_restaurant
    ).inner_join(
      gs_restaurant
    ).on(
      gs_restaurant.restaurant_id == gs_franchise_restaurant.restaurant_id
    ).select(
      gs_franchise_restaurant.restaurant_id,
      gs_restaurant.name,
      gs_restaurant.address1,
      gs_restaurant.city,
      gs_restaurant.state,
      gs_restaurant.postal,
      gs_restaurant.restaurant_type,
      gs_restaurant.thumbnail_url,
      gs_restaurant.phone_number
    ).where(
      gs_franchise_restaurant.franchise_id == franchise_id
    ).orderby(
      gs_restaurant.name, order=Order.asc
    )

    return gsdb.fetchall(str(qry))

  def get_restaurant_menus(self, restaurant_id: int):
    gs_menu, gs_restaurant_menu = Tables('gs_menu', 'gs_restaurant_menu')
    qry = Query.from_(
      gs_restaurant_menu
    ).inner_join(
      gs_menu
    ).on(
      gs_menu.menu_id == gs_restaurant_menu.menu_id
    ).select(
      gs_restaurant_menu.menu_id,
      gs_menu.name,
      gs_menu.description,
      gs_menu.thumbnail_url,
      gs_menu.label_color
    ).where(
      gs_restaurant_menu.restaurant_id == Parameter('%s')
    ).orderby(
      gs_menu.name, order=Order.asc
    )

    restaurants = gsdb.fetchall(str(qry), (restaurant_id,))

    return restaurants

  def add_restaurant(self, franchise_id: int, restaurant_id: int):
    gs_franchise_restaurant = Table('gs_franchise_restaurant')
    qry = Query.into(
      gs_franchise_restaurant
    ).columns(
      gs_franchise_restaurant.tenant_id,
      gs_franchise_restaurant.franchise_id,
      gs_franchise_restaurant.restaurant_id,
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s')
    )

    return gsdb.execute(str(qry), (franchise_id, restaurant_id,))

  def delete_restaurant(self, franchise_id: int, restaurant_id: int):
    gs_franchise_restaurant = Table('gs_franchise_restaurant')
    qry = Query.from_(
      gs_franchise_restaurant
    ).delete().where(
      gs_franchise_restaurant.franchise_id == Parameter('%s')
    ).where(
      gs_franchise_restaurant.restaurant_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (franchise_id, restaurant_id,))

  def restaurant_exists(self, franchise_id: int, restaurant_id: int):
    gs_franchise_restaurant = Table('gs_franchise_restaurant')
    qry = Query.from_(
      gs_franchise_restaurant
    ).select(
      '*'
    ).where(
      gs_franchise_restaurant.franchise_id == franchise_id
    ).where(
      gs_franchise_restaurant.restaurant_id == restaurant_id
    )
    
    restaurant = gsdb.fetchone(str(qry))

    if restaurant is not None:
      return True
    
    return False

  def get_restaurants_paginated(self, franchise_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    restaurants_list = []

    restaurants = self.get_restaurants(franchise_id)
    
    if restaurants != None:
      for restaurant in restaurants:
        restaurants_list.append(format_restaurant(restaurant))

    json_data, total_rows, total_pages = generate_paginated_data(restaurants_list, page, limit)

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