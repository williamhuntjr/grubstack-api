from grubstack import app, gsdb
from math import ceil

PER_PAGE = app.config['PER_PAGE']

def buildGramMeasurement(amount: int):
  measurement = {
    "value": amount,
    "unit": {
      "name": "grams",
      "abbreviation": "g",
    },
  }
  return measurement

def buildMilligramMeasurement(amount: int):
  measurement = {
    "value": amount,
    "unit": {
      "name": "milligrams",
      "abbreviation": "mg",
    },
  }
  return measurement

def formatIngredient(ingredient: dict):
  return {
    "id": ingredient['ingredient_id'],
    "name": ingredient['name'],
    "description": ingredient['description'],
    "thumbnail_url": ingredient['thumbnail_url'],
    "label_color": ingredient['label_color'],
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
  
def formatParams(params: dict):
  name = params['name']
  description = params['description'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']
  label_color = params['label_color'] or 'blue'
  calories = params['calories'] or 0.0
  fat = params['fat'] or 0.0
  saturated_fat = params['saturated_fat'] or 0.0
  trans_fat = params['trans_fat'] or 0.0
  cholesterol = params['cholesterol'] or 0.0
  sodium = params['sodium'] or 0.0
  carbs = params['carbs'] or 0.0
  protein = params['protein'] or 0.0
  sugar = params['sugar'] or 0.0
  fiber = params['fiber'] or 0.0
  price = params['price'] or 0.0

  return (name, description, thumbnail_url, label_color, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price)

def getIngredients(page: int = 1, limit: int = PER_PAGE):
  json_data = []
  ingredients = gsdb.fetchall("SELECT * FROM gs_ingredient ORDER BY name ASC")
  
  ingredients_list = []
  for ingredient in ingredients:
    ingredients_list.append(formatIngredient(ingredient))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(ingredients) / limit)
  total_rows = len(ingredients)

  # Get paged data
  json_data = ingredients_list[start:end]

  return (json_data, total_rows, total_pages)
