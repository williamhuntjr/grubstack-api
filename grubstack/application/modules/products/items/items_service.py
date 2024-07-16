from pypika import PostgreSQLQuery, Query, Table, Tables, Order, Parameter

from grubstack import app, gsdb
from grubstack.application.utilities.filters import generate_paginated_data
from grubstack.application.modules.products.ingredients.ingredients_utilities import format_ingredient
from grubstack.application.modules.products.varieties.varieties_utilities import format_variety

from .items_utilities import format_item
from .items_constants import PER_PAGE, DEFAULT_FILTERS

class ItemService:
  def __init__(self):
    pass

  def apply_filters(self, item: dict, filters: list = []):
    ingredients_list = []

    if 'showIngredients' in filters and filters['showIngredients']:
      ingredients = self.get_ingredients(item['item_id'])
      if ingredients != None:
        for ingredient in ingredients:
          ingredients_list.append(format_ingredient(ingredient))

    return format_item(item, ingredients_list, [], filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    if len(filters) <= 0:
      filters = DEFAULT_FILTERS

    gs_item = Table('gs_item')

    qry = Query.from_(
      gs_item
    ).select(
      '*'
    ).orderby(
      gs_item.name, order=Order.asc
    ) 

    items = gsdb.fetchall(str(qry))

    filtered = []

    for item in items:
      filtered.append(self.apply_filters(item, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, item_id: int, filters: list = []):
    gs_item = Table('gs_item')
    qry = Query.from_(
      gs_item
    ).select(
      '*'
    ).where(
      gs_item.item_id == item_id
    )

    item = gsdb.fetchone(str(qry))

    if item is not None:
      filtered_data = self.apply_filters(item, filters)
      return filtered_data

    else:
      return None

  def search(self, name: str, filters: list = []):
    gs_item = Table('gs_item')
    qry = Query.from_(
      gs_item
    ).select(
      '*'
    ).where(
      gs_item.name == Parameter('%s')
    )

    item = gsdb.fetchone(str(qry), (name,))

    if item is not None:
      filtered_data = self.apply_filters(item, filters)
      return filtered_data

    else:
      return None

  def get_by_slug(self, slug: str, filters: list = []):
    gs_item = Table('gs_item')
    qry = Query.from_(
      gs_item
    ).select(
      '*'
    ).where(
      gs_item.slug == Parameter('%s')
    )

    item = gsdb.fetchone(str(qry), (slug,))

    if item is not None:
      filtered_data = self.apply_filters(item, filters)
      return filtered_data

    else:
      return None

  def delete(self, item_id: int):
    gs_item = Table('gs_item')
    qry = Query.from_(
      gs_item
    ).delete().where(
      gs_item.item_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (item_id,))

    gs_menu_item = Table('gs_menu_item')
    qry = Query.from_(
      gs_menu_item
    ).delete().where(
      gs_menu_item.item_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (item_id,))

  def create(self, params: dict = ()):
    name, description, thumbnail_url, slug = params

    gs_item = Table('gs_item')
    qry = PostgreSQLQuery.into(
      gs_item
    ).columns(
      gs_item.tenant_id,
      gs_item.name,
      gs_item.description,
      gs_item.thumbnail_url,
      gs_item.slug
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s')
    ).returning('item_id')

    return gsdb.fetchone(str(qry), (name, description, thumbnail_url, slug,))

  def update(self, item_id: int, params: dict = ()):
    name, description, thumbnail_url, slug = params

    gs_item = Table('gs_item')
    qry = Query.update(
      gs_item
    ).set(
      gs_item.name, Parameter('%s')
    ).set(
      gs_item.description, Parameter('%s')
    ).set(
      gs_item.thumbnail_url, Parameter('%s')
    ).set(
      gs_item.slug, Parameter('%s')
    ).where(
      gs_item.item_id == Parameter('%s')
    )

    return gsdb.execute(str(qry), (name, description, thumbnail_url, slug, item_id,))

  def get_ingredients(self, item_id: int):
    gs_ingredient, gs_item_ingredient = Tables('gs_ingredient', 'gs_item_ingredient')
    qry = Query.from_(
      gs_item_ingredient
    ).inner_join(
      gs_ingredient
    ).on(
      gs_ingredient.ingredient_id == gs_item_ingredient.ingredient_id
    ).select(
      gs_item_ingredient.ingredient_id,
      gs_ingredient.name,
      gs_ingredient.description,
      gs_ingredient.thumbnail_url,
      gs_ingredient.calories,
      gs_ingredient.fat,
      gs_ingredient.saturated_fat,
      gs_ingredient.trans_fat,
      gs_ingredient.cholesterol,
      gs_ingredient.carbs,
      gs_ingredient.sodium,
      gs_ingredient.protein,
      gs_ingredient.sugar,
      gs_ingredient.fiber,
      gs_ingredient.price,
      gs_item_ingredient.is_optional,
      gs_item_ingredient.is_addon,
      gs_item_ingredient.is_extra
    ).where(
      gs_item_ingredient.item_id == Parameter('%s')
    ).orderby(
      gs_ingredient.name, order=Order.asc
    )

    return gsdb.fetchall(str(qry), (item_id,))

  def get_ingredients_paginated(self, item_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    ingredients = self.get_ingredients(item_id)

    ingredients_list = []
    if ingredients != None:
      for ingredient in ingredients:
        ingredients_list.append(format_ingredient(ingredient))

    json_data, total_rows, total_pages = generate_paginated_data(ingredients_list, page, limit)

    return (json_data, total_rows, total_pages)

  def ingredient_exists(self, item_id: int, ingredient_id: int):
    gs_item_ingredient = Table('gs_item_ingredient')
    qry = Query.from_(
      gs_item_ingredient
    ).select(
      '*'
    ).where(
      gs_item_ingredient.item_id == item_id
    ).where(
      gs_item_ingredient.ingredient_id == ingredient_id
    )
    
    ingredient = gsdb.fetchone(str(qry))

    if ingredient is not None:
      return True
    
    return False

  def add_ingredient(self, item_id: int, ingredient_id: int):
    gs_item_ingredient = Table('gs_item_ingredient')
    qry = Query.into(
      gs_item_ingredient
    ).columns(
      gs_item_ingredient.tenant_id,
      gs_item_ingredient.item_id,
      gs_item_ingredient.ingredient_id,
      gs_item_ingredient.is_optional,
      gs_item_ingredient.is_addon,
      gs_item_ingredient.is_extra
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      'f',
      'f',
      'f'
    )

    gsdb.execute(str(qry), (item_id, ingredient_id,))

  def delete_ingredient(self, item_id: int, ingredient_id: int):
    gs_item_ingredient = Table('gs_item_ingredient')
    qry = Query.from_(
      gs_item_ingredient
    ).delete().where(
      gs_item_ingredient.item_id == Parameter('%s')
    ).where(
      gs_item_ingredient.ingredient_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (item_id, ingredient_id,))

  def update_ingredient(self, item_id: int, ingredient_id: int, params: dict):
    is_optional, is_addon, is_extra = params

    gs_item_ingredient = Table('gs_item_ingredient')
    qry = Query.update(
      gs_item_ingredient
    ).set(
      gs_item_ingredient.is_optional, Parameter('%s')
    ).set(
      gs_item_ingredient.is_addon, Parameter('%s')
    ).set(
      gs_item_ingredient.is_extra, Parameter('%s')
    ).where(
      gs_item_ingredient.item_id == Parameter('%s')
    ).where(
      gs_item_ingredient.ingredient_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (is_optional, is_addon, is_extra, item_id, ingredient_id,))

  def get_item_ingredient(self, item_id: int, ingredient_id: int):
    gs_item_ingredient = Table('gs_item_ingredient')
    qry = Query.from_(
      gs_item_ingredient
    ).select(
      '*'
    ).where(
      gs_item_ingredient.item_id == Parameter('%s')
    ).where(
      gs_item_ingredient.ingredient_id == Parameter('%s')
    )

    return gsdb.fetchone(str(qry), (item_id, ingredient_id,))

  def get_varieties(self, item_id: int):
    gs_variety, gs_item_variety = Tables('gs_variety', 'gs_item_variety')
    qry = Query.from_(
      gs_item_variety
    ).inner_join(
      gs_variety
    ).on(
      gs_variety.variety_id == gs_item_variety.variety_id
    ).select(
      gs_item_variety.variety_id,
      gs_variety.name,
      gs_variety.description,
      gs_variety.thumbnail_url,
    ).where(
      gs_item_variety.item_id == Parameter('%s')
    ).orderby(
      gs_variety.name, order=Order.asc
    )

    return gsdb.fetchall(str(qry), (item_id,))

  def get_varieties_paginated(self, item_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    varieties = self.get_varieties(item_id)

    varieties_list = []
    if varieties != None:
      for variety in varieties:
        varieties_list.append(format_variety(variety))

    json_data, total_rows, total_pages = generate_paginated_data(varieties_list, page, limit)

    return (json_data, total_rows, total_pages)

  def variety_exists(self, item_id: int, variety_id: int):
    gs_item_variety = Table('gs_item_variety')
    qry = Query.from_(
      gs_item_variety
    ).select(
      '*'
    ).where(
      gs_item_variety.item_id == item_id
    ).where(
      gs_item_variety.variety_id == variety_id
    )
    
    variety = gsdb.fetchone(str(qry))

    if variety is not None:
      return True
    
    return False

  def add_variety(self, item_id: int, variety_id: int):
    gs_item_variety = Table('gs_item_variety')
    qry = Query.into(
      gs_item_variety
    ).columns(
      gs_item_variety.tenant_id,
      gs_item_variety.item_id,
      gs_item_variety.variety_id,
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s')
    )

    gsdb.execute(str(qry), (item_id, variety_id,))

  def delete_variety(self, item_id: int, variety_id: int):
    gs_item_variety = Table('gs_item_variety')
    qry = Query.from_(
      gs_item_variety
    ).delete().where(
      gs_item_variety.item_id == Parameter('%s')
    ).where(
      gs_item_variety.variety_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (item_id, variety_id,))