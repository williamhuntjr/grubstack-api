import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import AuthError, jwt_required, requires_permission

from grubstack.application.utilities.request import verify_params
from grubstack.application.utilities.filters import generate_filters, create_pagination_params

from grubstack.application.modules.products.items.items_service import ItemService

from .menus_utilities import format_menu, format_params, format_item_params
from .menus_constants import MENU_FILTERS, PER_PAGE, DEFAULT_FILTERS, REQUIRED_FIELDS
from .menus_service import MenuService

menu = Blueprint('menu', __name__)
logger = logging.getLogger('grubstack')

menu_service = MenuService()
item_service = ItemService()

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

@menu.route('/menus', methods=['POST'])
@jwt_required()
@requires_permission("MaintainMenus")
def create():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      verify_params(params, REQUIRED_FIELDS)

      name, description, thumbnail_url = format_params(params)
      
      name = params['name']
      menu = menu_service.search(name)

      if menu is not None:
        return gs_make_response(message='That menu already exists. Try a different name',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
      else:
        menu_id = menu_service.create(format_params(params))[0]
        menu = menu_service.get(menu_id)

        headers = {'Location': url_for('menu.get', menu_id=menu_id)}
        return gs_make_response(message='Menu created successfully',
                              httpstatus=201,
                              headers=headers,
                              data=menu)
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
    return gs_make_response(message='Unable to create menu',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menus/<int:menu_id>', methods=['GET'])
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

@menu.route('/menus/<int:menu_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainMenus")
def delete(menu_id: str):
  try:
    menu = menu_service.get(menu_id)

    if menu is None:
      return gs_make_response(message='Menu not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      menu_service.delete(menu_id)
      return gs_make_response(message=f'Menu #{menu_id} deleted')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menus/<int:menu_id>', methods=['PATCH'])
@jwt_required()
@requires_permission("MaintainMenus")
def update(menu_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      if menu_id:
        menu = menu_service.get(menu_id)

        if menu is None:
          return gs_make_response(message='Menu not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if 'name' in params:
          menu_search = menu_service.search(params['name'])
          if menu_search is not None and menu_search['id'] != menu_id:
            return gs_make_response(message='That menu already exists. Try a different name',
                      status=GStatusCode.ERROR,
                      httpstatus=400)

        menu_service.update(menu_id, format_params(params, menu))
        menu = menu_service.get(menu_id)

        headers = {'Location': url_for('menu.get', menu_id=menu_id)}
        return gs_make_response(message=f'Menu #{menu_id} updated',
                                httpstatus=201,
                                headers=headers,
                                data=menu)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update menu',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menus/<int:menu_id>/items', methods=['GET'])
@jwt_required()
@requires_permission("ViewMenus")
def get_all_items(menu_id: int):
  try:
    menu = menu_service.get(menu_id)

    if menu is None:
      return gs_make_response(message='Menu not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = menu_service.get_items_paginated(menu_id, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve items. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menus/<int:menu_id>/items', methods=['POST'])
@jwt_required()
@requires_permission("MaintainMenus")
def add_item(menu_id: str):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      item_id = params['item_id']

      if menu_id is not None and item_id is not None:
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
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menus/<int:menu_id>/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainMenus")
def delete_item(menu_id: str, item_id: str):
  try:
    is_existing = menu_service.item_exists(menu_id, item_id)

    if is_existing is None:
      return gs_make_response(message='Invalid menu item',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      menu_service.delete_item(menu_id, item_id)
      return gs_make_response(message=f'Item #{item_id} deleted from menu')
      
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menus/<int:menu_id>/items/<int:item_id>', methods=['PATCH'])
@jwt_required()
@requires_permission("MaintainMenus")
def update_item(menu_id: str, item_id: str):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      if menu_id is not None and item_id:
        menu = menu_service.get(menu_id)
        item = item_service.get(item_id)

        if menu is None:
          return gs_make_response(message='Menu not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if item is None:
          return gs_make_response(message='Item not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          is_existing = menu_service.item_exists(menu_id, item_id)

          if is_existing:
            menu_item = menu_service.get_menu_item(menu_id, item_id)
            menu_service.update_item(menu_id, item_id, format_item_params(params, menu_item))
            return gs_make_response(message=f'Item #{item_id} updated on menu')

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(menu, url_prefix=config.get('general', 'urlprefix', fallback='/'))
