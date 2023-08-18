from grubstack import app, gsdb
from math import ceil

PER_PAGE = app.config['PER_PAGE']

def formatVariety(variety: dict):
  return {
    "id": variety['variety_id'],
    "name": variety['name'],
    "description": variety['description'],
    "thumbnail_url": variety['thumbnail_url'],
  }

def formatParams(params: dict):
  name = params['name']
  description = params['description'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']

  return (name, description, thumbnail_url)

def getVarieties(page: int = 1, limit: int = PER_PAGE):
  json_data = []
  varieties = gsdb.fetchall("SELECT * FROM gs_variety ORDER BY name ASC")

  varieties_list = []
  for variety in varieties:
    varieties_list.append(formatVariety(variety))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(varieties) / limit)
  total_rows = len(varieties)

  # Get paged data
  json_data = varieties_list[start:end]

  return (json_data, total_rows, total_pages)

def getVarietyIngredients(varietyId, page: int = 1, limit: int = PER_PAGE):
  json_data = []
  ingredients = gsdb.fetchall("""SELECT c.ingredient_id, name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, carbs, sodium, protein, sugar, fiber
                                  FROM gs_ingredient c INNER JOIN gs_variety_ingredient p ON p.ingredient_id = c.ingredient_id 
                                  WHERE p.variety_id = %s ORDER BY name ASC""", (varietyId,))

  ingredients_list = []
  for ingredient in ingredients:
    ingredients_list.append({
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
    })

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(ingredients) / limit)
  total_rows = len(ingredients)

  # Get paged data
  json_data = ingredients_list[start:end]

  return (json_data, total_rows, total_pages)
