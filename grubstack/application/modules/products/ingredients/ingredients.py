import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission

from grubstack.application.utilities.request import verify_params
from grubstack.application.utilities.filters import generate_filters, create_pagination_params

from .ingredients_utilities import format_params
from .ingredients_constants import INGREDIENT_FILTERS, REQUIRED_FIELDS

from .ingredients_service import IngredientService

ingredient = Blueprint('ingredient', __name__)
logger = logging.getLogger('grubstack')

ingredient_service = IngredientService()

@ingredient.route('/ingredients', methods=['GET'])
@jwt_required()
@requires_permission("ViewIngredients", "MaintainIngredients")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)
    json_data, total_rows, total_pages = ingredient_service.get_all(page, limit, generate_filters(INGREDIENT_FILTERS, request.args))

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve ingredients. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredients', methods=['POST'])
@jwt_required()
@requires_permission("MaintainIngredients")
def create():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      verify_params(params, REQUIRED_FIELDS)

      name, description, thumbnail_url, calories, fat, saturated_fat, trans_fat, cholesterol, sodium, carbs, protein, sugar, fiber, price = format_params(params)
      
      name = params['name']
      ingredient = ingredient_service.search(name)

      if ingredient is not None:
        return gs_make_response(message='That ingredient already exists. Try a different name',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
      else:
        ingredient_id = ingredient_service.create(format_params(params))[0]
        ingredient = ingredient_service.get(ingredient_id)

        headers = {'Location': url_for('ingredient.get', ingredient_id=ingredient_id)}
        return gs_make_response(message='Ingredient created successfully',
                              httpstatus=201,
                              headers=headers,
                              data=ingredient)
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
    return gs_make_response(message='Unable to create ingredient',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredients/<int:ingredient_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewIngredients", "MaintainIngredients")
def get(ingredient_id: int):
  try:
    ingredient = ingredient_service.get(ingredient_id, generate_filters(INGREDIENT_FILTERS, request.args))

    if ingredient:
      return gs_make_response(data=ingredient)

    else:
      return gs_make_response(message='Ingredient not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredients/<int:ingredient_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainIngredients")
def delete(ingredient_id: int):
  try:
    ingredient = ingredient_service.get(ingredient_id)

    if ingredient is None:
      return gs_make_response(message='Ingredient not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      qry = ingredient_service.delete(ingredient_id)
      return gs_make_response(message=f'Ingredient #{ingredient_id} deleted')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@ingredient.route('/ingredients/<int:ingredient_id>', methods=['PATCH'])
@jwt_required()
@requires_permission("MaintainIngredients")
def update(ingredient_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      if ingredient_id:
        ingredient = ingredient_service.get(ingredient_id)

        if ingredient is None:
          return gs_make_response(message='Ingredient not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if 'name' in params:
          ingredient_search = ingredient_service.search(params['name'])
          if ingredient_search is not None and ingredient_search['id'] != ingredient_id:
            return gs_make_response(message='That ingredient already exists. Try a different name',
                      status=GStatusCode.ERROR,
                      httpstatus=400)

        ingredient_service.update(ingredient_id, format_params(params, ingredient))
        ingredient = ingredient_service.get(ingredient_id)

        headers = {'Location': url_for('ingredient.get', ingredient_id=ingredient['id'])}
        return gs_make_response(message=f'Ingredient #{ingredient_id} updated',
                                httpstatus=201,
                                headers=headers,
                                data=ingredient)

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
