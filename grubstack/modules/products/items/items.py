import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission

item = Blueprint('item', __name__)
logger = logging.getLogger('grubstack')
per_page = app.config['PER_PAGE']

def formatItems(item: dict, varieties_list: list):
  return {
    "id": item['item_id'],
    "name": item['name'],
    "description": item['description'],
    "thumbnail_url": item['thumbnail_url'],
    "varieties": varieties_list
  }

@item.route('/items', methods=['GET'])
@requires_auth
@requires_permission("ViewItems")
def get_all():
  try:
    json_data = []
    items = gsdb.fetchall("SELECT * FROM gs_item ORDER BY name ASC")
    
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = per_page
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

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

    # Get paged data
    json_data = items_list[start:end]

    return gs_make_response(data=json_data, totalrowcount=len(items), totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve items. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/create', methods=['POST'])
@requires_auth
@requires_permission("MaintainItems")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      name = params['name']
      description = params['description'] or ''
      thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']

      if name:
        # Check if exists
        row = gsdb.fetchall("SELECT * from gs_item WHERE name = %s", (name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That item already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_item
                                (tenant_id, item_id, name, description, thumbnail_url)
                                VALUES 
                                (%s, DEFAULT, %s, %s, %s)""", (app.config["TENANT_ID"], name, description, thumbnail_url,))
          row = gsdb.fetchone("SELECT * FROM gs_item WHERE name = %s", (name,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('item.get', item_id=row['item_id'])}
            return gs_make_response(message=f'Item {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=row)
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create item',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/<string:item_id>', methods=['GET'])
@requires_auth
@requires_permission("ViewItems")
def get(item_id: int):
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)

      # Check if exists
      row = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))
      if row: 
        varieties = gsdb.fetchall("""SELECT c.variety_id, name, description, thumbnail_url
                            FROM gs_variety c INNER JOIN gs_item_variety p ON p.variety_id = c.variety_id 
                            WHERE p.item_id = %s ORDER BY name ASC""", (row['item_id'],))

        varieties_list = []
        for variety in varieties:
          varieties_list.append({
            "id": variety['variety_id'],
            "name": variety['name'],
            "description": variety['description'],
            "thumbnail_url": variety['thumbnail_url'],
          })

        json_data = formatItems(row, varieties_list)

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/delete', methods=['POST'])
@requires_auth
@requires_permission("MaintainItems")
def delete():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      item_id = params['item_id']

      if item_id:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))
        if row is None:
          return gs_make_response(message='Invalid item',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_item WHERE item_id = %s", (item_id,))
          qry = gsdb.execute("DELETE FROM gs_item_ingredient WHERE item_id = %s", (item_id,))
          return gs_make_response(message=f'Item #{item_id} deleted')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/update', methods=['POST'])
@requires_auth
@requires_permission("MaintainItems")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      item_id = params['id']
      name = params['name']
      description = params['description'] 
      thumbnail_url = params['thumbnail_url']

      if item_id and name and description and thumbnail_url:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))

        if row is None:
          return gs_make_response(message=f'Item {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_item SET (name, description, thumbnail_url) = (%s, %s, %s) WHERE item_id = %s", (name, description, thumbnail_url, item_id,))
          headers = {'Location': url_for('item.get', item_id=item_id)}
          return gs_make_response(message=f'Item {name} successfully updated',
                    httpstatus=201,
                    headers=headers,
                    data=json_data)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update item',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/<int:itemId>', methods=['GET'])
@requires_auth
@requires_permission("ViewItems")
def get_item(itemId):
  try:
    json_data = {}
    item = gsdb.fetchone("""SELECT item_id, name, description, thumbnail_url FROM gs_item WHERE item_id = %s""", (itemId,))
    if item:
      json_data = {
        "id": item['item_id'],
        "name": item['name'],
        "description": item['description'],
        "thumbnail_url": item['thumbnail_url'],
      }
      return gs_make_response(data=json_data)

    else:
      return gs_make_response(message='Invalid item ID',
                              status=GStatusCode.ERROR,
                              httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve item. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/<int:itemId>/ingredients', methods=['GET'])
@requires_auth
@requires_permission("ViewItems")
def get_all_ingredients(itemId):
  try:
    json_data = []
    ingredients = gsdb.fetchall("""SELECT c.ingredient_id, name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, carbs, sodium, protein, sugar, fiber, is_optional, is_addon, is_extra
                                    FROM gs_ingredient c INNER JOIN gs_item_ingredient p ON p.ingredient_id = c.ingredient_id 
                                    WHERE p.item_id = %s ORDER BY name ASC""", (itemId,))
    
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = per_page
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

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

    # Get paged data
    json_data = ingredients_list[start:end]

    return gs_make_response(data=json_data, totalrowcount=len(ingredients), totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve ingredients. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/addIngredient', methods=['POST'])
@requires_auth
@requires_permission("MaintainItems")
def add_ingredient():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      item_id = params['item_id']
      ingredient_id = params['ingredient_id']

      if item_id and ingredient_id:
        # Check if exists
        item = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))
        ingredient = gsdb.fetchone("SELECT * FROM gs_ingredient WHERE ingredient_id = %s", (ingredient_id,))
        is_existing = gsdb.fetchone("SELECT * FROM gs_item_ingredient WHERE item_id = %s AND ingredient_id = %s", (item_id, ingredient_id,))
        if item is None or ingredient is None:
          return gs_make_response(message='Invalid item or invalid ingredient',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          if not is_existing:
            qry = gsdb.execute("""INSERT INTO gs_item_ingredient 
                                  (tenant_id, item_id, ingredient_id, is_optional, is_addon, is_extra)
                                  VALUES 
                                  (%s, %s, %s, 'f', 'f', 'f')""", (app.config["TENANT_ID"], item_id, ingredient_id,))
            return gs_make_response(message=f'Ingredient #{ingredient_id} added to item')
          else:
            return gs_make_response(message=f'Ingredient already exists on item',
                                    status=GStatusCode.ERROR,
                                    httpstatus=400)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/updateIngredient', methods=['POST'])
@requires_auth
@requires_permission("MaintainItems")
def update_ingredient():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      item_id = params['item_id']
      ingredient_id = params['ingredient_id']
      is_optional = params['is_optional']
      is_addon = params['is_addon']
      is_extra = params['is_extra']

      if item_id is not None and ingredient_id is not None and is_optional is not None and is_addon is not None and is_extra is not None:
        # Check if exists
        item = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))
        ingredient = gsdb.fetchone("SELECT * FROM gs_ingredient WHERE ingredient_id = %s", (ingredient_id,))
        is_existing = gsdb.fetchone("SELECT * FROM gs_item_ingredient WHERE item_id = %s AND ingredient_id = %s", (item_id, ingredient_id,))
        if item is None or ingredient is None:
          return gs_make_response(message='Invalid item or invalid ingredient',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          if is_existing:
            qry = gsdb.execute("UPDATE gs_item_ingredient SET is_optional = %s, is_addon = %s, is_extra = %s WHERE item_id = %s AND ingredient_id = %s", (is_optional, is_addon, is_extra, item_id, ingredient_id,))
            return gs_make_response(message=f'Ingredient #{ingredient_id} updated on item')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/deleteIngredient', methods=['POST'])
@requires_auth
@requires_permission("MaintainItems")
def delete_ingredient():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      item_id = params['item_id']
      ingredient_id = params['ingredient_id']

      if item_id and ingredient_id:
        # Check if exists
        item = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))
        item_ingredient = gsdb.fetchone("SELECT * FROM gs_item_ingredient WHERE item_id = %s AND ingredient_id = %s", (item_id, ingredient_id,))
        if item is None or item_ingredient is None:
          return gs_make_response(message='Invalid item or invalid ingredient',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_item_ingredient WHERE item_id = %s AND ingredient_id = %s", (item_id, ingredient_id,))
          return gs_make_response(message=f'Ingredient #{ingredient_id} deleted from item')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/<int:itemId>/varieties', methods=['GET'])
@requires_auth
@requires_permission("ViewItems")
def get_all_varieties(itemId):
  try:
    json_data = []
    varieties = gsdb.fetchall("""SELECT c.variety_id, name, description, thumbnail_url
                                    FROM gs_variety c INNER JOIN gs_item_variety p ON p.variety_id = c.variety_id 
                                    WHERE p.item_id = %s ORDER BY name ASC""", (itemId,))

    for variety in varieties:
      json_data.append({
        "id": variety['variety_id'],
        "name": variety['name'],
        "description": variety['description'],
        "thumbnail_url": variety['thumbnail_url'],
      })

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve varieties. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/addVariety', methods=['POST'])
@requires_auth
@requires_permission("MaintainItems")
def add_variety():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      item_id = params['item_id']
      variety_id = params['variety_id']

      if item_id and variety_id:
        # Check if exists
        item = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))
        variety = gsdb.fetchone("SELECT * FROM gs_variety WHERE variety_id = %s", (variety_id,))
        is_existing = gsdb.fetchone("SELECT * FROM gs_item_variety WHERE item_id = %s AND variety_id = %s", (item_id, variety_id,))
        if item is None or variety is None:
          return gs_make_response(message='Invalid item or invalid variety',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          if not is_existing:
            qry = gsdb.execute("INSERT INTO gs_item_variety VALUES (%s, %s, %s)", (app.config["TENANT_ID"], item_id, variety_id,))
            return gs_make_response(message=f'Variety #{variety_id} added to item')
          else:
            return gs_make_response(message=f'Variety already exists on item',
                                    status=GStatusCode.ERROR,
                                    httpstatus=400)
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/deleteVariety', methods=['POST'])
@requires_auth
@requires_permission("MaintainItems")
def delete_variety():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      item_id = params['item_id']
      variety_id = params['variety_id']

      if item_id and variety_id:
        # Check if exists
        item_variety = gsdb.fetchone("SELECT * FROM gs_item_variety WHERE item_id = %s AND variety_id = %s", (item_id, variety_id,))
        if item_variety is None:
          return gs_make_response(message='Invalid item variety',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_item_variety WHERE item_id = %s AND variety_id = %s", (item_id, variety_id,))
          return gs_make_response(message=f'Variety #{variety_id} deleted from item')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(item, url_prefix=config.get('general', 'urlprefix', fallback='/'))
