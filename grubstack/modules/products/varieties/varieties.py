import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission

variety = Blueprint('variety', __name__)
logger = logging.getLogger('grubstack')
per_page = app.config['PER_PAGE']

def formatVariety(variety: dict):
  return {
    "id": variety['variety_id'],
    "name": variety['name'],
    "description": variety['description'],
    "thumbnail_url": variety['thumbnail_url'],
  }

@variety.route('/varieties', methods=['GET'])
@requires_auth
@requires_permission("ViewVarieties")
def get_all():
  try:
    json_data = []
    varieties = gsdb.fetchall("SELECT * FROM gs_variety ORDER BY name ASC")
    
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = per_page
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    varieties_list = []
    for variety in varieties:
      varieties_list.append(formatVariety(variety))

    # Calculate paged data
    offset = page - 1
    start = offset * limit
    end = start + limit
    total_pages = ceil(len(varieties) / limit)

    # Get paged data
    json_data = varieties_list[start:end]

    return gs_make_response(data=json_data, totalrowcount=len(varieties), totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve varieties. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/create', methods=['POST'])
@requires_auth
@requires_permission("MaintainVarieties")
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
        row = gsdb.fetchall("SELECT * from gs_variety WHERE name = %s", (name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That variety already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_variety
                                (tenant_id, variety_id, name, description, thumbnail_url)
                                VALUES 
                                (%s, DEFAULT, %s, %s, %s)""", (app.config["TENANT_ID"], name, description, thumbnail_url,))
          row = gsdb.fetchone("SELECT * FROM gs_variety WHERE name = %s", (name,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('variety.get', variety_id=row['variety_id'])}
            return gs_make_response(message=f'Variety {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=row)
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create variety',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/<string:variety_id>', methods=['GET'])
@requires_auth
@requires_permission("ViewVarieties")
def get(variety_id: int):
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)

      # Check if exists
      row = gsdb.fetchone("SELECT * FROM gs_variety WHERE variety_id = %s", (variety_id,))
      if row: 
        json_data = formatVariety(row)

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/delete', methods=['POST'])
@requires_auth
@requires_permission("MaintainVarieties")
def delete():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      variety_id = params['variety_id']

      if variety_id:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_variety WHERE variety_id = %s", (variety_id,))
        if row is None:
          return gs_make_response(message='Invalid variety',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_variety WHERE variety_id = %s", (variety_id,))
          return gs_make_response(message=f'Variety #{variety_id} deleted')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/update', methods=['POST'])
@requires_auth
@requires_permission("MaintainVarieties")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      variety_id = params['id']
      name = params['name']
      description = params['description'] 
      thumbnail_url = params['thumbnail_url']

      if variety_id and name and description and thumbnail_url:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_variety WHERE variety_id = %s", (variety_id,))

        if row is None:
          return gs_make_response(message=f'Variety {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_variety SET (name, description, thumbnail_url) = (%s, %s, %s) WHERE variety_id = %s", (name, description, thumbnail_url, variety_id,))
          headers = {'Location': url_for('variety.get', variety_id=variety_id)}
          return gs_make_response(message=f'Variety {name} successfully updated',
                    httpstatus=201,
                    headers=headers,
                    data=json_data)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update variety',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/<int:varietyId>', methods=['GET'])
@requires_auth
@requires_permission("ViewVarieties")
def get_variety(varietyId):
  try:
    json_data = {}
    variety = gsdb.fetchone("""SELECT variety_id, name, description, thumbnail_url FROM gs_variety WHERE variety_id = %s""", (varietyId,))
    if variety:
      json_data = {
        "id": variety['variety_id'],
        "name": variety['name'],
        "description": variety['description'],
        "thumbnail_url": variety['thumbnail_url'],
      }
      return gs_make_response(data=json_data)

    else:
      return gs_make_response(message='Invalid variety ID',
                              status=GStatusCode.ERROR,
                              httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve variety. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/<int:varietyId>/ingredients', methods=['GET'])
@requires_auth
@requires_permission("ViewVarieties")
def get_all_ingredients(varietyId):
  try:
    json_data = []
    ingredients = gsdb.fetchall("""SELECT c.ingredient_id, name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, carbs, sodium, protein, sugar, fiber
                                    FROM gs_ingredient c INNER JOIN gs_variety_ingredient p ON p.ingredient_id = c.ingredient_id 
                                    WHERE p.variety_id = %s ORDER BY name ASC""", (varietyId,))
    
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

@variety.route('/variety/addIngredient', methods=['POST'])
@requires_auth
@requires_permission("MaintainVarieties")
def add_ingredient():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      variety_id = params['variety_id']
      ingredient_id = params['ingredient_id']

      if variety_id and ingredient_id:
        # Check if exists
        variety = gsdb.fetchone("SELECT * FROM gs_variety WHERE variety_id = %s", (variety_id,))
        ingredient = gsdb.fetchone("SELECT * FROM gs_ingredient WHERE ingredient_id = %s", (ingredient_id,))
        is_existing = gsdb.fetchone("SELECT * FROM gs_variety_ingredient WHERE variety_id = %s AND ingredient_id = %s", (variety_id, ingredient_id,))
        if variety is None or ingredient is None:
          return gs_make_response(message='Invalid variety or invalid ingredient',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          if not is_existing:
            qry = gsdb.execute("""INSERT INTO gs_variety_ingredient 
                                  (tenant_id, variety_id, ingredient_id)
                                  VALUES 
                                  (%s, %s, %s)""", (app.config["TENANT_ID"], variety_id, ingredient_id,))
            return gs_make_response(message=f'Ingredient #{ingredient_id} added to variety')
          else:
            return gs_make_response(message=f'Ingredient already exists on variety',
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

@variety.route('/variety/deleteIngredient', methods=['POST'])
@requires_auth
@requires_permission("MaintainVarieties")
def delete_ingredient():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      variety_id = params['variety_id']
      ingredient_id = params['ingredient_id']

      if variety_id and ingredient_id:
        # Check if exists
        variety = gsdb.fetchone("SELECT * FROM gs_variety WHERE variety_id = %s", (variety_id,))
        variety_ingredient = gsdb.fetchone("SELECT * FROM gs_variety_ingredient WHERE variety_id = %s AND ingredient_id = %s", (variety_id, ingredient_id,))
        if variety is None or variety_ingredient is None:
          return gs_make_response(message='Invalid variety or invalid ingredient',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_variety_ingredient WHERE variety_id = %s AND ingredient_id = %s", (variety_id, ingredient_id,))
          return gs_make_response(message=f'Ingredient #{ingredient_id} deleted from variety')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(variety, url_prefix=config.get('general', 'urlprefix', fallback='/'))
 