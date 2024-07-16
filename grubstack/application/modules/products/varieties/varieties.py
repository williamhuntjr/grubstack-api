import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission

from grubstack.application.utilities.request import verify_params
from grubstack.application.utilities.filters import generate_filters, create_pagination_params

from grubstack.application.modules.products.ingredients.ingredients_service import IngredientService

from .varieties_utilities import format_variety, format_params
from .varieties_constants import VARIETY_FILTERS, REQUIRED_FIELDS
from .varieties_service import VarietyService

variety = Blueprint('variety', __name__)
logger = logging.getLogger('grubstack')

variety_service = VarietyService()
ingredient_service = IngredientService()

@variety.route('/varieties', methods=['GET'])
@jwt_required()
@requires_permission("ViewVarieties", "MaintainVarieties")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)
    json_data, total_rows, total_pages = variety_service.get_all(page, limit, generate_filters(VARIETY_FILTERS, request.args))

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve varieties. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/varieties', methods=['POST'])
@jwt_required()
@requires_permission("MaintainVarieties")
def create():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      verify_params(params, REQUIRED_FIELDS)

      name, description, thumbnail_url = format_params(params)
      
      name = params['name']
      variety = variety_service.search(name)

      if variety is not None:
        return gs_make_response(message='A variety with the provided name already exists. Try a different name',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
      else:
        variety_id = variety_service.create(format_params(params))[0]
        variety = variety_service.get(variety_id)

        headers = {'Location': url_for('variety.get', variety_id=variety_id)}
        return gs_make_response(message='Variety created successfully',
                              httpstatus=201,
                              headers=headers,
                              data=variety)
    else:
      return gs_make_response(message='Invalid request',
                              status=GStatusCode.ERROR,
                              httpstatus=400)

  except ValueError as e:
    return gs_make_response(message=e,
                            status=GStatusCode.ERROR,
                            httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create variety',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/varieties/<int:variety_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewVarieties", "MaintainVarieties")
def get(variety_id: int):
  try:
    variety = variety_service.get(variety_id, generate_filters(VARIETY_FILTERS, request.args))

    if variety:
      return gs_make_response(data=variety)

    else:
      return gs_make_response(message='Variety not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/varieties/<int:variety_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainVarieties")
def delete(variety_id: int):
  try:
    variety = variety_service.get(variety_id)

    if variety is None:
      return gs_make_response(message='Variety not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      qry = variety_service.delete(variety_id)
      return gs_make_response(message=f'Variety #{variety_id} deleted')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/varieties/<int:variety_id>', methods=['PATCH'])
@jwt_required()
@requires_permission("MaintainVarieties")
def update(variety_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      if variety_id:
        variety = variety_service.get(variety_id)

        if variety is None:
          return gs_make_response(message='Variety not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if 'name' in params:
          variety_search = variety_service.search(params['name'])
          if variety_search is not None and variety_search['id'] != variety_id:
            return gs_make_response(message='A variety with the provided name already exists. Try a different name',
                      status=GStatusCode.ERROR,
                      httpstatus=400)

        variety_service.update(variety_id, format_params(params, variety))
        variety = variety_service.get(variety_id)

        headers = {'Location': url_for('variety.get', variety_id=variety_id)}
        return gs_make_response(message=f'Variety #{variety_id} updated',
                                httpstatus=201,
                                headers=headers,
                                data=variety)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update variety',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/varieties/<int:variety_id>/ingredients', methods=['GET'])
@jwt_required()
@requires_permission("ViewVarieties", "MaintainVarieties")
def get_all_ingredients(variety_id):
  try:
    variety = variety_service.get(variety_id, generate_filters(VARIETY_FILTERS, request.args))

    if variety is None:
      return gs_make_response(message='Variety not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      page, limit = create_pagination_params(request.args)

      json_data, total_rows, total_pages = variety_service.get_ingredients_paginated(variety_id, page, limit)

      return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve ingredients. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@variety.route('/varieties/<int:variety_id>/ingredients', methods=['POST'])
@jwt_required()
@requires_permission("MaintainVarieties")
def add_ingredient(variety_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      ingredient_id = params['ingredient_id']

      if ingredient_id is not None and variety_id is not None:
        variety = variety_service.get(variety_id)
        ingredient = ingredient_service.get(ingredient_id)
        
        if variety is None:
          return gs_make_response(message='Variety not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if ingredient is None:
          return gs_make_response(message='Ingredient not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          is_existing = variety_service.ingredient_exists(variety_id, ingredient_id)

          if not is_existing:
            variety_service.add_ingredient(variety_id, ingredient_id)
            
            return gs_make_response(message=f'Ingredient #{ingredient_id} added to variety', httpstatus=201)
          else:
            return gs_make_response(message='The provided Ingredient already exists on the specified variety',
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

@variety.route('/varieties/<int:variety_id>/ingredients/<int:ingredient_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainVarieties")
def delete_ingredient(variety_id: int, ingredient_id: int):
  try:
    is_existing = variety_service.ingredient_exists(variety_id, ingredient_id)

    if is_existing is None:
      return gs_make_response(message='Variety ingredient does not exist',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      variety_service.delete_ingredient(variety_id, ingredient_id)
      return gs_make_response(message=f'Ingredient #{ingredient_id} deleted from variety')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(variety, url_prefix=config.get('general', 'urlprefix', fallback='/'))
 