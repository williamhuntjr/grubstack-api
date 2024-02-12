from math import ceil
import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import AuthError, jwt_required, requires_permission
from grubstack.application.utilities.filters import generate_filters, create_pagination_params

from .menus_utilities import format_menu, getMenus, format_params, format_item_params
from .menus_constants import MENU_FILTERS, PER_PAGE, DEFAULT_FILTERS
from .menus_service import MenuService

menu = Blueprint('menu', __name__)
logger = logging.getLogger('grubstack')

menu_service = MenuService()

@menu.route('/menus', methods=['GET'])
@jwt_required()
@requires_permission("ViewMenus")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = menu_service.get_all(page, limit, generate_filters(MENU_FILTERS, request.args))

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve menus. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/create', methods=['POST'])
@jwt_required()
@requires_permission("MaintainMenus")
def create():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      name = params['name']

      if name:
        menu = menu_service.search(name)

        if menu is not None:
          return gs_make_response(message='That menu already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          menu_service.create(format_params(params))
          menu = menu_service.search(name)

          if menu is not None:
            headers = {'Location': url_for('menu.get', menu_id=menu['id'])}
            return gs_make_response(message=f'Menu {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=menu)
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create menu',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/<string:menu_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewMenus")
def get(menu_id: int, showVarieties: bool = False):
  try:
    menu = menu_service.get(menu_id, DEFAULT_FILTERS)
    
    if menu:
      return gs_make_response(data=menu)

    else:
      return gs_make_response(message='Menu not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/delete', methods=['POST'])
@jwt_required()
@requires_permission("MaintainMenus")
def delete():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['menu_id']

      if menu_id:
        menu = menu_service.get(menu_id)

        if menu is None:
          return gs_make_response(message='Menu not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          menu_service.delete(menu_id)
          return gs_make_response(message=f'Menu #{menu_id} deleted')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/update', methods=['POST'])
@jwt_required()
@requires_permission("MaintainMenus")
def update():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['id']
      name = params['name']

      if menu_id and name:
        menu = menu_service.get(menu_id)

        if menu is None:
          return gs_make_response(message=f'Menu not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          menu_service.update(menu_id, format_params(params))
          headers = {'Location': url_for('menu.get', menu_id=menu_id)}
          return gs_make_response(message=f'Menu {name} successfully updated',
                    httpstatus=201,
                    headers=headers)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update menu',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/<int:menuId>/items', methods=['GET'])
@jwt_required()
@requires_permission("ViewMenus")
def get_all_items(menuId: int):
  try:
    menu = menu_service.get(menuId)

    if menu is None:
      return gs_make_response(message='Menu not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
                              
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = menu_service.get_items_paginated(menuId, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve items. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/addItem', methods=['POST'])
@jwt_required()
@requires_permission("MaintainMenus")
def add_item():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['menu_id']
      item_id = params['item_id']

      if menu_id is not None and item_id is not None:
        # Check if exists
        menu = menu_service.get(menu_id)
        item = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))

        is_existing = menu_service.item_exists(menu_id, item_id)
        
        if menu is None:
          return gs_make_response(message='Menu not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if item is None:
          return gs_make_response(message='Item not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          if not is_existing:
            menu_service.add_item(menu_id, item_id, format_item_params(params))

            return gs_make_response(message=f'Item #{item_id} added to menu', httpstatus=201)
          else:
            return gs_make_response(message=f'Item already exists on menu',
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

@menu.route('/menu/deleteItem', methods=['POST'])
@jwt_required()
@requires_permission("MaintainMenus")
def delete_item():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['menu_id']
      item_id = params['item_id']

      if menu_id and item_id:
        is_existing = menu_service.item_exists(menu_id, item_id)

        if is_existing is None:
          return gs_make_response(message='Invalid menu item',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)

        else:
          menu_service.delete_item(menu_id, item_id)
          return gs_make_response(message=f'Item #{item_id} deleted from menu')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/updateItem', methods=['POST'])
@jwt_required()
@requires_permission("MaintainMenus")
def update_item():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['menu_id']
      item_id = params['item_id']

      if menu_id is not None and item_id:
        is_existing = menu_service.item_exists(menu_id, item_id)

        if is_existing is None:
          return gs_make_response(message='Menu item not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          menu_service.update_item(menu_id, item_id, format_item_params(params))
          return gs_make_response(message=f'Item #{item_id} updated on menu')
        
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(menu, url_prefix=config.get('general', 'urlprefix', fallback='/'))
