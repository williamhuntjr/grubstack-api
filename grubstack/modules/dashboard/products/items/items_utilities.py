from grubstack import app, gsdb
from math import ceil

PER_PAGE = app.config['PER_PAGE']

def formatItems(item: dict, varieties_list: list):
  return {
    "id": item['item_id'],
    "name": item['name'],
    "description": item['description'],
    "thumbnail_url": item['thumbnail_url'],
    "varieties": varieties_list
  }
  
def formatParams(params: dict):
  name = params['name']
  description = params['description'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']

  return (name, description, thumbnail_url)

def getItems(page: int = 1, limit: int = PER_PAGE):
  json_data = []
  items = gsdb.fetchall("SELECT * FROM gs_item ORDER BY name ASC")
  
  items_list = []
  for item in items:
    varieties = gsdb.fetchall("""SELECT c.variety_id, name, description, thumbnail_url
                        FROM gs_variety c INNER JOIN gs_item_variety p ON p.variety_id = c.variety_id 
                        WHERE p.item_id = %s ORDER BY name ASC""", (item['item_id'],))

    varieties_list = []
    for variety in varieties:
      varieties_list.append({
        "id": variety['variety_id'],
        "name": variety['name'],
        "description": variety['description'],
        "thumbnail_url": variety['thumbnail_url'],
      })

    items_list.append(formatItems(item, varieties_list))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(items) / limit)
  total_rows = len(items)

  # Get paged data
  json_data = items_list[start:end]

  return (json_data, total_rows, total_pages)

def getItemIngredients(itemId, page: int = 1, limit: int = PER_PAGE):
  json_data = []
  ingredients = gsdb.fetchall("""SELECT c.ingredient_id, name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, carbs, sodium, protein, sugar, fiber, is_optional, is_addon, is_extra
                                  FROM gs_ingredient c INNER JOIN gs_item_ingredient p ON p.ingredient_id = c.ingredient_id 
                                  WHERE p.item_id = %s ORDER BY name ASC""", (itemId,))

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
      "is_optional": ingredient['is_optional'],
      "is_addon": ingredient['is_addon'],
      "is_extra": ingredient['is_extra'],
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