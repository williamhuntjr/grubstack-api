import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission

from grubstack.application.utilities.request import verify_params
from grubstack.application.utilities.filters import generate_filters, create_pagination_params

from grubstack.application.modules.products.ingredients.ingredients_service import IngredientService
from grubstack.application.modules.products.varieties.varieties_service import VarietyService

from .items_utilities import format_item, format_params, format_ingredient_params
from .items_constants import ITEM_FILTERS, REQUIRED_FIELDS
from .items_service import ItemService

item = Blueprint('item', __name__)
logger = logging.getLogger('grubstack')

item_service = ItemService()
ingredient_service = IngredientService()
variety_service = VarietyService()

@item.route('/items', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems", "MaintainItems")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)
    json_data, total_rows, total_pages = item_service.get_all(page, limit, generate_filters(ITEM_FILTERS, request.args))

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve items. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items', methods=['POST'])
@jwt_required()
@requires_permission("MaintainItems")
def create():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      verify_params(params, REQUIRED_FIELDS)

      name, description, thumbnail_url = format_params(params)
      
      name = params['name']
      item = item_service.search(name)

      if item is not None:
        return gs_make_response(message='That item already exists. Try a different name',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
      else:
        item_id = item_service.create(format_params(params))[0]
        item = item_service.get(item_id)

        headers = {'Location': url_for('item.get', item_id=item_id)}
        return gs_make_response(message='Item created successfully',
                              httpstatus=201,
                              headers=headers,
                              data=item)
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
    return gs_make_response(message='Unable to create item',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<int:item_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems", "MaintainItems")
def get(item_id: int):
  try:
    item = item_service.get(item_id, generate_filters(ITEM_FILTERS, request.args))

    if item:
      return gs_make_response(data=item)

    else:
      return gs_make_response(message='Item not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainItems")
def delete(item_id: int):
  try:
    item = item_service.get(item_id)

    if item is None:
      return gs_make_response(message='Item not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      qry = item_service.delete(item_id)
      return gs_make_response(message=f'Item #{item_id} deleted')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<int:item_id>', methods=['PATCH'])
@jwt_required()
@requires_permission("MaintainItems")
def update(item_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      if item_id:
        item = item_service.get(item_id)

        if item is None:
          return gs_make_response(message='Item not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if 'name' in params:
          item_search = item_service.search(params['name'])
          if item_search is not None and item_search['id'] != item_id:
            return gs_make_response(message='That item already exists. Try a different name',
                      status=GStatusCode.ERROR,
                      httpstatus=400)

        item_service.update(item_id, format_params(params, item))
        item = item_service.get(item_id)

        headers = {'Location': url_for('item.get', item_id=item_id)}
        return gs_make_response(message=f'Item #{item_id} updated',
                                httpstatus=201,
                                headers=headers,
                                data=item)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update item',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<int:item_id>/ingredients', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems", "MaintainItems")
def get_all_ingredients(item_id: int):
  try:
    item = item_service.get(item_id, generate_filters(ITEM_FILTERS, request.args))

    if item is None:
      return gs_make_response(message='Item not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

    else:
      page, limit = create_pagination_params(request.args)

      json_data, total_rows, total_pages = item_service.get_ingredients_paginated(item_id, page, limit)

      return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve ingredients. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<int:item_id>/ingredients', methods=['POST'])
@jwt_required()
@requires_permission("MaintainItems")
def add_ingredient(item_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      ingredient_id = params['ingredient_id']

      if ingredient_id is not None and item_id is not None:
        item = item_service.get(item_id)
        ingredient = ingredient_service.get(ingredient_id)
        
        if item is None:
          return gs_make_response(message='Item not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if ingredient is None:
          return gs_make_response(message='Ingredient not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          is_existing = item_service.ingredient_exists(item_id, ingredient_id)

          if not is_existing:
            item_service.add_ingredient(item_id, ingredient_id)
            
            return gs_make_response(message=f'Ingredient #{ingredient_id} added to item', httpstatus=201)
          else:
            return gs_make_response(message='Ingredient already exists on item',
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

@item.route('/items/<int:item_id>/ingredients/<int:ingredient_id>', methods=['PATCH'])
@jwt_required()
@requires_permission("MaintainItems")
def update_ingredient(item_id: int, ingredient_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      if item_id is not None and ingredient_id:
        item = item_service.get(item_id)
        ingredient = ingredient_service.get(ingredient_id)

        if item is None:
          return gs_make_response(message='Item not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if ingredient is None:
          return gs_make_response(message='Ingredient not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          is_existing = item_service.ingredient_exists(item_id, ingredient_id)

          if is_existing:
            item_ingredient = item_service.get_item_ingredient(item_id, ingredient_id)
            item_service.update_ingredient(item_id, ingredient_id, format_ingredient_params(params, item_ingredient))
            return gs_make_response(message=f'Ingredient #{ingredient_id} updated on item')

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<int:item_id>/ingredients/<int:ingredient_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainItems")
def delete_ingredient(item_id: int, ingredient_id: int):
  try:
    is_existing = item_service.ingredient_exists(item_id, ingredient_id)

    if is_existing is None:
      return gs_make_response(message='Item ingredient does not exist',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      item_service.delete_ingredient(item_id, ingredient_id)
      return gs_make_response(message=f'Ingredient #{ingredient_id} deleted from item')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<int:item_id>/varieties', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems", "MaintainItems")
def get_all_varieties(item_id: str):
  try:
    item = item_service.get(item_id, generate_filters(ITEM_FILTERS, request.args))

    if item is None:
      return gs_make_response(message='Item not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      page, limit = create_pagination_params(request.args)

      json_data, total_rows, total_pages = item_service.get_varieties_paginated(item_id, page, limit)

      return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve varieties. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)


@item.route('/items/<int:item_id>/varieties', methods=['POST'])
@jwt_required()
@requires_permission("MaintainItems")
def add_variety(item_id: str):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      variety_id = params['variety_id']

      if variety_id is not None and item_id is not None:
        item = item_service.get(item_id)
        variety = variety_service.get(variety_id)
        
        if item is None:
          return gs_make_response(message='Item not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if variety is None:
          return gs_make_response(message='Variety not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          is_existing = item_service.variety_exists(item_id, variety_id)

          if not is_existing:
            item_service.add_variety(item_id, variety_id)
            
            return gs_make_response(message=f'Variety #{variety_id} added to item', httpstatus=201)
          else:
            return gs_make_response(message='Variety already exists on item',
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

@item.route('/items/<int:item_id>/varieties/<int:variety_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainItems")
def delete_variety(item_id: int, variety_id: int):
  try:
    is_existing = item_service.variety_exists(item_id, variety_id)

    if is_existing is None:
      return gs_make_response(message='Item variety does not exist',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      item_service.delete_variety(item_id, variety_id)
      return gs_make_response(message=f'Variety #{variety_id} deleted from item')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(item, url_prefix=config.get('general', 'urlprefix', fallback='/'))
