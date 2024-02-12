from math import ceil
import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission
from grubstack.application.utilities.filters import generate_filters, create_pagination_params

from .items_utilities import formatItem, getItems, getItemIngredients, formatParams, getAllItemIngredients, getAllItemVarieties

item = Blueprint('item', __name__)
logger = logging.getLogger('grubstack')
PER_PAGE = app.config['PER_PAGE']

@item.route('/items', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = getItems(page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve items. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/create', methods=['POST'])
@jwt_required()
@requires_permission("MaintainItems")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      name, description, thumbnail_url, label_color = formatParams(params)

      if name:
        # Check if exists
        row = gsdb.fetchall("SELECT * from gs_item WHERE name = %s", (name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That item already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_item
                                (tenant_id, item_id, name, description, thumbnail_url, label_color)
                                VALUES 
                                (%s, DEFAULT, %s, %s, %s, %s)""", (app.config["TENANT_ID"], name, description, thumbnail_url, label_color))
          row = gsdb.fetchone("SELECT * FROM gs_item WHERE name = %s", (name,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('item.get', itemId=row['item_id'])}
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

@item.route('/item/<string:itemId>', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems")
def get(itemId: int):
  try:
    json_data = {}

    # Check if exists
    row = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (itemId,))
    if row: 
      ingredients_list = getAllItemIngredients(itemId)
      varieties_list = getAllItemVarieties(itemId)

      json_data = formatItem(row, ingredients_list, varieties_list)
    else:
      return gs_make_response(message='Invalid item ID',
                              status=GStatusCode.ERROR,
                              httpstatus=400)

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/delete', methods=['POST'])
@jwt_required()
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
@jwt_required()
@requires_permission("MaintainItems")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      item_id = params['id']
      name, description, thumbnail_url, label_color = formatParams(params)

      if item_id and name and description and thumbnail_url:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))

        if row is None:
          return gs_make_response(message=f'Item {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_item SET (name, description, thumbnail_url, label_color) = (%s, %s, %s, %s) WHERE item_id = %s", (name, description, thumbnail_url, label_color, item_id,))
          headers = {'Location': url_for('item.get', itemId=item_id)}
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

@item.route('/item/<int:itemId>/ingredients', methods=['GET'])
@jwt_required()
@requires_permission("ViewItems")
def get_all_ingredients(itemId):
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = getItemIngredients(itemId, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve ingredients. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/addIngredient', methods=['POST'])
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
@requires_permission("ViewItems")
def get_all_varieties(itemId):
  try:
    varieties_list = getAllItemVarieties(itemId)

    return gs_make_response(data=varieties_list)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve varieties. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@item.route('/item/addVariety', methods=['POST'])
@jwt_required()
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
@jwt_required()
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
