from pypika import PostgreSQLQuery, Query, Table, Order, Parameter

from grubstack import app, gsdb
from grubstack.application.utilities.filters import generate_paginated_data

from .ingredients_utilities import format_ingredient
from .ingredients_constants import PER_PAGE

class IngredientService:
  def __init__(self):
    pass

  def apply_filters(self, ingredient: dict, filters: dict = {}):
    return format_ingredient(ingredient, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: dict = {}):
    gs_ingredient = Table('gs_ingredient')

    qry = Query.from_(
      gs_ingredient
    ).select(
      '*'
    ).orderby(
      gs_ingredient.name, order=Order.asc
    ) 

    ingredients = gsdb.fetchall(str(qry))

    filtered = []

    for ingredient in ingredients:
      filtered.append(self.apply_filters(ingredient, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, ingredient_id: int, filters: dict = {}):
    gs_ingredient = Table('gs_ingredient')
    qry = Query.from_(
      gs_ingredient
    ).select(
      '*'
    ).where(
      gs_ingredient.ingredient_id == ingredient_id
    )

    ingredient = gsdb.fetchone(str(qry))

    if ingredient is not None:
      filtered_data = self.apply_filters(ingredient, filters)
      return filtered_data

    else:
      return None

  def search(self, name: str, filters: dict = {}):
    gs_ingredient = Table('gs_ingredient')
    qry = Query.from_(
      gs_ingredient
    ).select(
      '*'
    ).where(
      gs_ingredient.name == name
    )

    ingredient = gsdb.fetchone(str(qry))

    if ingredient is not None:
      filtered_data = self.apply_filters(ingredient, filters)
      return filtered_data

    else:
      return None

  def delete(self, ingredient_id: int):
    gs_ingredient = Table('gs_ingredient')
    qry = Query.from_(
      gs_ingredient
    ).delete().where(
      gs_ingredient.ingredient_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (ingredient_id,))

    gs_item_ingredient = Table('gs_item_ingredient')
    qry = Query.from_(
      gs_item_ingredient
    ).delete().where(
      gs_item_ingredient.ingredient_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (ingredient_id,))
  
  def update(self, ingredient_id: int, params: dict = ()):
    name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price = params

    gs_ingredient = Table('gs_ingredient')
    qry = Query.update(
      gs_ingredient
    ).set(
      gs_ingredient.name, Parameter('%s')
    ).set(
      gs_ingredient.description, Parameter('%s')
    ).set(
      gs_ingredient.thumbnail_url, Parameter('%s')
    ).set(
      gs_ingredient.calories, Parameter('%s')
    ).set(
      gs_ingredient.fat, Parameter('%s')
    ).set(
      gs_ingredient.saturated_fat, Parameter('%s')
    ).set(
      gs_ingredient.trans_fat, Parameter('%s')
    ).set(
      gs_ingredient.cholesterol, Parameter('%s')
    ).set(
      gs_ingredient.sodium, Parameter('%s')
    ).set(
      gs_ingredient.carbs, Parameter('%s')
    ).set(
      gs_ingredient.protein, Parameter('%s')
    ).set(
      gs_ingredient.sugar, Parameter('%s')
    ).set(
      gs_ingredient.fiber, Parameter('%s')
    ).set(
      gs_ingredient.price, Parameter('%s')
    ).where(
      gs_ingredient.ingredient_id == Parameter('%s')
    )

    return gsdb.execute(str(qry), (name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price, ingredient_id,))

  def create(self, params: dict = ()):
    name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price = params

    gs_ingredient = Table('gs_ingredient')
    qry = PostgreSQLQuery.into(
      gs_ingredient
    ).columns(
      gs_ingredient.tenant_id,
      gs_ingredient.name,
      gs_ingredient.description,
      gs_ingredient.thumbnail_url,
      gs_ingredient.calories,
      gs_ingredient.fat,
      gs_ingredient.saturated_fat,
      gs_ingredient.trans_fat,
      gs_ingredient.cholesterol,
      gs_ingredient.sodium,
      gs_ingredient.carbs,
      gs_ingredient.protein,
      gs_ingredient.sugar,
      gs_ingredient.fiber,
      gs_ingredient.price
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
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s')
    ).returning('ingredient_id')

    return gsdb.fetchone(str(qry), (name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price,))
