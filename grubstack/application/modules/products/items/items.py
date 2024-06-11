import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission

from grubstack.application.utilities.request import verify_params
from grubstack.application.utilities.filters import generate_filters, create_pagination_params

from .items_utilities import format_item, getItemIngredients, format_params, getAllItemIngredients, getAllItemVarieties
from .items_constants import ITEM_FILTERS, REQUIRED_FIELDS
from .items_service import ItemService

item = Blueprint('item', __name__)
logger = logging.getLogger('grubstack')

item_service = ItemService()

@item.route('/items', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems")
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
        item_service.create(format_params(params))
        item = item_service.search(name)

        headers = {'Location': url_for('item.get', item_id=item['id'])}
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

@item.route('/items/<string:item_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems")
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

@item.route('/items/<string:item_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainItems")
def delete(item_id: str):
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

        headers = {'Location': url_for('item.get', item_id=item['id'])}
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
@requires_permission("ViewItems")
def get_all_ingredients(item_id):
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = getItemIngredients(item_id, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve ingredients. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<string:item_id>/ingredients', methods=['POST'])
@jwt_required()
@requires_permission("MaintainItems")
def add_ingredient(item_id: str):
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
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
                                  (%s, %s, %s, 'f', 'f', 'f')""", (app.config['TENANT_ID'], item_id, ingredient_id,))
            return gs_make_response(message=f'Ingredient #{ingredient_id} added to item')
          else:
            return gs_make_response(message=f'Ingredient already exists on item',
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

@item.route('/items/<string:item_id>/ingredients', methods=['PUT'])
@jwt_required()
@requires_permission("MaintainItems")
def update_ingredient(item_id: str):
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
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
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<string:item_id>/ingredients/<string:ingredient_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainItems")
def delete_ingredient(item_id: str, ingredient_id: str):
  try:
    item = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))
    item_ingredient = gsdb.fetchone("SELECT * FROM gs_item_ingredient WHERE item_id = %s AND ingredient_id = %s", (item_id, ingredient_id,))
    if item is None or item_ingredient is None:
      return gs_make_response(message='Invalid item or invalid ingredient',
                              status=GStatusCode.ERROR,
                              httpstatus=400)
    else:
      qry = gsdb.execute("DELETE FROM gs_item_ingredient WHERE item_id = %s AND ingredient_id = %s", (item_id, ingredient_id,))
      return gs_make_response(message=f'Ingredient #{ingredient_id} deleted from item')
      
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<string:item_id>/varieties', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems")
def get_all_varieties(item_id: str):
  try:
    varieties_list = getAllItemVarieties(item_id)

    return gs_make_response(data=varieties_list)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve varieties. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/items/<string:item_id>/varieties', methods=['POST'])
@jwt_required()
@requires_permission("MaintainItems")
def add_variety(item_id: str):
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
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
            qry = gsdb.execute("INSERT INTO gs_item_variety VALUES (%s, %s, %s)", (app.config['TENANT_ID'], item_id, variety_id,))
            return gs_make_response(message=f'Variety #{variety_id} added to item')
          else:
            return gs_make_response(message=f'Variety already exists on item',
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

@item.route('/items/<string:item_id>/<string:variety_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainItems")
def delete_variety(item_id: str, variety_id: str):
  try:
    item_variety = gsdb.fetchone("SELECT * FROM gs_item_variety WHERE item_id = %s AND variety_id = %s", (item_id, variety_id,))
    if item_variety is None:
      return gs_make_response(message='Invalid item variety',
                              status=GStatusCode.ERROR,
                              httpstatus=400)
    else:
      qry = gsdb.execute("DELETE FROM gs_item_variety WHERE item_id = %s AND variety_id = %s", (item_id, variety_id,))
      return gs_make_response(message=f'Variety #{variety_id} deleted from item')
      
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(item, url_prefix=config.get('general', 'urlprefix', fallback='/'))
