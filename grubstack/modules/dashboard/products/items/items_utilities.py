from grubstack import app, gsdb
from math import ceil

PER_PAGE = app.config['PER_PAGE']

def formatItems(item: dict, ingredients_list, varieties_list: list):
  return {
    "id": item['item_id'],
    "name": item['name'],
    "description": item['description'],
    "thumbnail_url": item['thumbnail_url'],
    "label_color": item['label_color'],
    "ingredients": ingredients_list,
    "varieties": varieties_list
  }
  
def formatParams(params: dict):
  name = params['name']
  description = params['description'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']
  label_color = params['label_color'] or 'blue'

  return (name, description, thumbnail_url, label_color)

def getAllItemIngredients(itemId):
  ingredients = gsdb.fetchall("""SELECT c.ingredient_id, name, description, thumbnail_url, label_color, calories, fat, saturated_fat, trans_fat, cholesterol, carbs, sodium, protein, sugar, fiber, price, is_optional, is_addon, is_extra
                                FROM gs_ingredient c INNER JOIN gs_item_ingredient p ON p.ingredient_id = c.ingredient_id 
                                WHERE p.item_id = %s ORDER BY name ASC""", (itemId,))
  ingredients_list = []
  for ingredient in ingredients:
    ingredients_list.append({
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
      "price": ingredient['price'],
      "is_optional": ingredient['is_optional'],
      "is_addon": ingredient['is_addon'],
      "is_extra": ingredient['is_extra'],
    })
  return ingredients_list

def getAllItemVarieties(itemId):
  varieties = gsdb.fetchall("""SELECT c.variety_id, name, description, thumbnail_url, label_color
                      FROM gs_variety c INNER JOIN gs_item_variety p ON p.variety_id = c.variety_id 
                      WHERE p.item_id = %s ORDER BY name ASC""", (itemId,))
  varieties_list = []
  for variety in varieties:
    varieties_list.append({
      "id": variety['variety_id'],
      "name": variety['name'],
      "description": variety['description'],
      "thumbnail_url": variety['thumbnail_url'],
      "label_color": variety['label_color'],
    })
  return varieties_list

def getItems(page: int = 1, limit: int = PER_PAGE):
  json_data = []
  items = gsdb.fetchall("SELECT * FROM gs_item ORDER BY name ASC")
  
  items_list = []
  for item in items:
    ingredients_list = getAllItemIngredients(item['item_id'])
    varieties_list = getAllItemVarieties(item['item_id'])

    items_list.append(formatItems(item, ingredients_list, varieties_list))

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
  ingredients = getAllItemIngredients(itemId)

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(ingredients) / limit)
  total_rows = len(ingredients)

  # Get paged data
  json_data = ingredients[start:end]

  return (json_data, total_rows, total_pages)
