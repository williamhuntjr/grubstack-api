import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.application.utilities.filters import generate_filters, create_pagination_params
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission
from .ingredients_utilities import buildGramMeasurement, buildMilligramMeasurement, formatIngredient, getIngredients, formatParams

ingredient = Blueprint('ingredient', __name__)
logger = logging.getLogger('grubstack')

PER_PAGE = app.config['PER_PAGE']

@ingredient.route('/ingredients', methods=['GET'])
@jwt_required()
@requires_permission("ViewIngredients")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = getIngredients(page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve ingredients. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredient/create', methods=['POST'])
@jwt_required()
@requires_permission("MaintainIngredients")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      name, description, thumbnail_url, label_color, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price = formatParams(params)
      
      if name:
        # Check if exists
        row = gsdb.fetchall("SELECT * from gs_ingredient WHERE name = %s", (name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That ingredient already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_ingredient
                                (tenant_id, ingredient_id, name, description, thumbnail_url, label_color, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price)
                                VALUES
                                (%s, DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            """, (app.config['TENANT_ID'], name, description, thumbnail_url, label_color, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price,))
          row = gsdb.fetchone("SELECT * FROM gs_ingredient WHERE name = %s", (name,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('ingredient.get', ingredient_id=row['ingredient_id'])}
            return gs_make_response(message=f'Ingredient {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=row)
      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create ingredient',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredient/<string:ingredient_id>', methods=['GET'])
@jwt_required()
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
@jwt_required()
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
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredient/update', methods=['POST'])
@jwt_required()
@requires_permission("MaintainIngredients")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      ingredient_id = params['id']
      name, description, thumbnail_url, label_color, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price = formatParams(params)

      if ingredient_id and name != None:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_ingredient WHERE ingredient_id = %s", (ingredient_id,))

        if row is None:
          return gs_make_response(message=f'Ingredient {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_ingredient SET (name, description, thumbnail_url, label_color, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price) = (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) WHERE ingredient_id = %s", (name, description, thumbnail_url, label_color, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price, ingredient_id,))
          headers = {'Location': url_for('ingredient.get', ingredient_id=ingredient_id)}
          return gs_make_response(message=f'Ingredient {name} successfully updated',
                    httpstatus=201,
                    headers=headers,
                    data=json_data)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update ingredient',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(ingredient, url_prefix=config.get('general', 'urlprefix', fallback='/'))
