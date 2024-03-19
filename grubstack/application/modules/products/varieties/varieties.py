import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission
from .varieties_utilities import formatVariety, getVarieties, formatParams, getVarietyIngredients

variety = Blueprint('variety', __name__)
logger = logging.getLogger('grubstack')

PER_PAGE = app.config['PER_PAGE']

@variety.route('/varieties', methods=['GET'])
@jwt_required()
@requires_permission("ViewVarieties")
def get_all():
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    json_data, total_rows, total_pages = getVarieties(page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve varieties. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/create', methods=['POST'])
@jwt_required()
@requires_permission("MaintainVarieties")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      name, description, thumbnail_url, label_color = formatParams(params)

      if name:
        # Check if exists
        row = gsdb.fetchall("SELECT * from gs_variety WHERE name = %s", (name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That variety already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_variety
                                (tenant_id, variety_id, name, description, thumbnail_url, label_color)
                                VALUES 
                                (%s, DEFAULT, %s, %s, %s, %s)""", (app.config['TENANT_ID'], name, description, thumbnail_url, label_color,))
          row = gsdb.fetchone("SELECT * FROM gs_variety WHERE name = %s", (name,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('variety.get', variety_id=row['variety_id'])}
            return gs_make_response(message=f'Variety {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=row)
      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create variety',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/<string:variety_id>', methods=['GET'])
@jwt_required()
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
@jwt_required()
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
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/update', methods=['POST'])
@jwt_required()
@requires_permission("MaintainVarieties")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      variety_id = params['id']
      name, description, thumbnail_url, label_color = formatParams(params)

      if variety_id and name and description and thumbnail_url:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_variety WHERE variety_id = %s", (variety_id,))

        if row is None:
          return gs_make_response(message=f'Variety {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_variety SET (name, description, thumbnail_url, label_color) = (%s, %s, %s, %s) WHERE variety_id = %s", (name, description, thumbnail_url, label_color, variety_id,))
          headers = {'Location': url_for('variety.get', variety_id=variety_id)}
          return gs_make_response(message=f'Variety {name} successfully updated',
                    httpstatus=201,
                    headers=headers,
                    data=json_data)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update variety',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/<int:variety_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewVarieties")
def get_variety(variety_id):
  try:
    json_data = {}
    row = gsdb.fetchone("""SELECT variety_id, name, description, thumbnail_url, label_color FROM gs_variety WHERE variety_id = %s""", (variety_id,))
    if variety:
      json_data = formatVariety(row)
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

@variety.route('/variety/<int:variety_id>/ingredients', methods=['GET'])
@jwt_required()
@requires_permission("ViewVarieties")
def get_all_ingredients(variety_id):
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    json_data, total_rows, total_pages = getVarietyIngredients(variety_id, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve ingredients. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/addIngredient', methods=['POST'])
@jwt_required()
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
                                  (%s, %s, %s)""", (app.config['TENANT_ID'], variety_id, ingredient_id,))
            return gs_make_response(message=f'Ingredient #{ingredient_id} added to variety')
          else:
            return gs_make_response(message=f'Ingredient already exists on variety',
                                    status=GStatusCode.ERROR,
                                    httpstatus=400)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/variety/deleteIngredient', methods=['POST'])
@jwt_required()
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
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(variety, url_prefix=config.get('general', 'urlprefix', fallback='/'))
 