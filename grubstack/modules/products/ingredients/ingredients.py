import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission

ingredient = Blueprint('ingredient', __name__)
logger = logging.getLogger('grubstack')
per_page = app.config['PER_PAGE']

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

@ingredient.route('/ingredients', methods=['GET'])
@requires_auth
@requires_permission("ViewIngredients")
def get_all():
  try:
    json_data = []
    ingredients = gsdb.fetchall("SELECT * FROM gs_ingredient ORDER BY name ASC")
    
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = per_page
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    ingredients_list = []
    for ingredient in ingredients:
      ingredients_list.append(formatIngredient(ingredient))

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

@ingredient.route('/ingredient/create', methods=['POST'])
@requires_auth
@requires_permission("MaintainIngredients")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      name = params['name']
      description = params['description'] or ''
      thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']
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

      if name:
        # Check if exists
        row = gsdb.fetchall("SELECT * from gs_ingredient WHERE name = %s", (name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That ingredient already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_ingredient
                                (tenant_id, ingredient_id, name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price)
                                VALUES
                                (%s, DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            """, (app.config["TENANT_ID"], name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price,))
          row = gsdb.fetchone("SELECT * FROM gs_ingredient WHERE name = %s", (name,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('ingredient.get', ingredient_id=row['ingredient_id'])}
            return gs_make_response(message=f'Ingredient {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=row)
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create ingredient',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredient/<string:ingredient_id>', methods=['GET'])
@requires_auth
@requires_permission("ViewIngredients")
def get(ingredient_id: int):
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)

      # Check if exists
      row = gsdb.fetchone("SELECT * FROM gs_ingredient WHERE ingredient_id = %s", (ingredient_id,))
      if row: 
        json_data = formatIngredient(row)

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredient/delete', methods=['POST'])
@requires_auth
@requires_permission("MaintainIngredients")
def delete():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      ingredient_id = params['ingredient_id']

      if ingredient_id:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_ingredient WHERE ingredient_id = %s", (ingredient_id,))
        if row is None:
          return gs_make_response(message='Invalid ingredient',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_ingredient WHERE ingredient_id = %s", (ingredient_id,))
          return gs_make_response(message=f'Ingredient #{ingredient_id} deleted')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredient/update', methods=['POST'])
@requires_auth
@requires_permission("MaintainIngredients")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      ingredient_id = params['id']
      name = params['name']
      description = params['description'] 
      thumbnail_url = params['thumbnail_url']
      calories = params['calories']
      fat = params['fat']
      saturated_fat = params['saturated_fat']
      trans_fat = params['trans_fat']
      cholesterol = params['cholesterol']
      sodium = params['sodium']
      carbs = params['carbs']
      protein = params['protein']
      sugar = params['sugar']
      fiber = params['fiber']
      price = params['price']

      if ingredient_id and name and description and thumbnail_url and calories is not None and fat is not None and saturated_fat is not None and trans_fat is not None and cholesterol is not None and sodium is not None and carbs is not None and protein is not None and sugar is not None and fiber is not None and price is not None:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_ingredient WHERE ingredient_id = %s", (ingredient_id,))

        if row is None:
          return gs_make_response(message=f'Ingredient {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_ingredient SET (name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price) = (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) WHERE ingredient_id = %s", (name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price, ingredient_id,))
          headers = {'Location': url_for('ingredient.get', ingredient_id=ingredient_id)}
          return gs_make_response(message=f'Ingredient {name} successfully updated',
                    httpstatus=201,
                    headers=headers,
                    data=json_data)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update ingredient',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(ingredient, url_prefix=config.get('general', 'urlprefix', fallback='/'))
