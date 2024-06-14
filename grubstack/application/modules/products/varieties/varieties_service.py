from pypika import PostgreSQLQuery, Query, Table, Tables, Order, Parameter

from grubstack import app, gsdb

from grubstack.application.modules.products.ingredients.ingredients_utilities import format_ingredient
from grubstack.application.utilities.filters import generate_paginated_data

from .varieties_utilities import format_variety
from .varieties_constants import PER_PAGE, DEFAULT_FILTERS

class VarietyService:
  def __init__(self):
    pass

  def apply_filters(self, variety: dict, filters: list = []):
    ingredients_list = []

    if 'showIngredients' in filters and filters['showIngredients']:
      ingredients = self.get_ingredients(variety['variety_id'])
      if ingredients != None:
        for ingredient in ingredients:
          ingredients_list.append(format_ingredient(ingredient))

    return format_variety(variety, ingredients_list, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    if len(filters) <= 0:
      filters = DEFAULT_FILTERS

    gs_variety = Table('gs_variety')

    qry = Query.from_(
      gs_variety
    ).select(
      '*'
    ).orderby(
      gs_variety.name, order=Order.asc
    ) 

    varieties = gsdb.fetchall(str(qry))

    filtered = []

    for variety in varieties:
      filtered.append(self.apply_filters(variety, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, variety_id: int, filters: list = []):
    if len(filters) <= 0:
      filters = DEFAULT_FILTERS

    gs_variety = Table('gs_variety')
    qry = Query.from_(
      gs_variety
    ).select(
      '*'
    ).where(
      gs_variety.variety_id == variety_id
    )

    variety = gsdb.fetchone(str(qry))

    if variety is not None:
      filtered_data = self.apply_filters(variety, filters)
      return filtered_data

    else:
      return None

  def search(self, name: str, filters: list = []):
    gs_variety = Table('gs_variety')
    qry = Query.from_(
      gs_variety
    ).select(
      '*'
    ).where(
      gs_variety.name == name
    )

    variety = gsdb.fetchone(str(qry))

    if variety is not None:
      filtered_data = self.apply_filters(variety, filters)
      return filtered_data

    else:
      return None

  def delete(self, variety_id: int):
    gs_variety = Table('gs_variety')
    qry = Query.from_(
      gs_variety
    ).delete().where(
      gs_variety.variety_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (variety_id,))

    gs_item_variety = Table('gs_item_variety')
    qry = Query.from_(
      gs_item_variety
    ).delete().where(
      gs_item_variety.variety_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (variety_id,))

  def create(self, params: dict = ()):
    name, description, thumbnail_url = params

    gs_variety = Table('gs_variety')
    qry = PostgreSQLQuery.into(
      gs_variety
    ).columns(
      gs_variety.tenant_id,
      gs_variety.name,
      gs_variety.description,
      gs_variety.thumbnail_url
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s')
    ).returning('variety_id')

    return gsdb.fetchone(str(qry), (name, description, thumbnail_url,))

  def update(self, variety_id: int, params: dict = ()):
    name, description, thumbnail_url = params

    gs_variety = Table('gs_variety')
    qry = Query.update(
      gs_variety
    ).set(
      gs_variety.name, Parameter('%s')
    ).set(
      gs_variety.description, Parameter('%s')
    ).set(
      gs_variety.thumbnail_url, Parameter('%s')
    ).where(
      gs_variety.variety_id == Parameter('%s')
    )

    return gsdb.execute(str(qry), (name, description, thumbnail_url, variety_id,))

  def get_ingredients(self, variety_id: int):
    gs_ingredient, gs_variety_ingredient = Tables('gs_ingredient', 'gs_variety_ingredient')
    qry = Query.from_(
      gs_variety_ingredient
    ).inner_join(
      gs_ingredient
    ).on(
      gs_ingredient.ingredient_id == gs_variety_ingredient.ingredient_id
    ).select(
      gs_variety_ingredient.ingredient_id,
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
      gs_ingredient.price
    ).where(
      gs_variety_ingredient.variety_id == Parameter('%s')
    ).orderby(
      gs_ingredient.name, order=Order.asc
    )

    return gsdb.fetchall(str(qry), (variety_id,))

  def get_ingredients_paginated(self, variety_id: int, page: int = 1, limit: int = PER_PAGE):
    json_data = []
    ingredients = self.get_ingredients(variety_id)

    ingredients_list = []
    if ingredients != None:
      for ingredient in ingredients:
        ingredients_list.append(format_ingredient(ingredient))

    json_data, total_rows, total_pages = generate_paginated_data(ingredients_list, page, limit)

    return (json_data, total_rows, total_pages)

  def ingredient_exists(self, variety_id: int, ingredient_id: int):
    gs_variety_ingredient = Table('gs_variety_ingredient')
    qry = Query.from_(
      gs_variety_ingredient
    ).select(
      '*'
    ).where(
      gs_variety_ingredient.variety_id == variety_id
    ).where(
      gs_variety_ingredient.ingredient_id == ingredient_id
    )
    
    ingredient = gsdb.fetchone(str(qry))

    if ingredient is not None:
      return True
    
    return False

  def add_ingredient(self, variety_id: int, ingredient_id: int):
    gs_variety_ingredient = Table('gs_variety_ingredient')
    qry = Query.into(
      gs_variety_ingredient
    ).columns(
      gs_variety_ingredient.tenant_id,
      gs_variety_ingredient.variety_id,
      gs_variety_ingredient.ingredient_id
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s')
    )

    gsdb.execute(str(qry), (variety_id, ingredient_id,))

  def delete_ingredient(self, variety_id: int, ingredient_id: int):
    gs_variety_ingredient = Table('gs_variety_ingredient')
    qry = Query.from_(
      gs_variety_ingredient
    ).delete().where(
      gs_variety_ingredient.variety_id == Parameter('%s')
    ).where(
      gs_variety_ingredient.ingredient_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (variety_id, ingredient_id,))
