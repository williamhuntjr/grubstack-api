from grubstack import app

from grubstack.application.utilities.reducers import field_reducer

from .ingredients_constants import PER_PAGE

def format_ingredient(ingredient: dict, filters: dict = {}):
  json_data = {
    "id": ingredient['ingredient_id'],
    "name": ingredient['name'],
    "description": ingredient['description'],
    "thumbnail_url": ingredient['thumbnail_url'],
    "calories": ingredient['calories'],
    "fat": ingredient['fat'],
    "saturated_fat": ingredient['saturated_fat'],
    "trans_fat": ingredient['trans_fat'],
    "cholesterol": ingredient['cholesterol'],
    "sodium": ingredient['sodium'],
    "carbs": ingredient['carbs'],
    "protein": ingredient['protein'],
    "sugar": ingredient['sugar'],
    "fiber": ingredient['fiber'],
    "price": ingredient['price']
  }

  if 'is_optional' in ingredient:
    json_data['is_optional'] = ingredient['is_optional']

  if 'is_addon' in ingredient:
    json_data['is_addon'] = ingredient['is_addon']

  if 'is_extra' in ingredient:
    json_data['is_extra'] = ingredient['is_extra']

  return json_data

def format_params(params: dict, ingredient: dict = {}):
  name = field_reducer('name', params, ingredient, '')
  description = field_reducer('description', params, ingredient, '')
  thumbnail_url = field_reducer('thumbnail_url', params, ingredient, app.config['THUMBNAIL_PLACEHOLDER_IMG'])
  calories = field_reducer('calories', params, ingredient, 0.0)
  fat = field_reducer('fat', params, ingredient, 0.0)
  saturated_fat = field_reducer('saturated_fat', params, ingredient, 0.0)
  trans_fat = field_reducer('trans_fat', params, ingredient, 0.0)
  cholesterol = field_reducer('cholesterol', params, ingredient, 0.0)
  sodium = field_reducer('sodium', params, ingredient, 0.0)
  carbs = field_reducer('carbs', params, ingredient, 0.0)
  protein = field_reducer('protein', params, ingredient, 0.0)
  sugar = field_reducer('sugar', params, ingredient, 0.0)
  fiber = field_reducer('fiber', params, ingredient, 0.0)
  price = field_reducer('price', params, ingredient, 0.0)

  return (name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price)
