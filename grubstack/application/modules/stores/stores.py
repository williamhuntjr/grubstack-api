import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission
from grubstack.application.utilities.filters import generate_filters, create_pagination_params
from grubstack.application.modules.products.menus.menus_service import MenuService

from .stores_utilities import format_store, format_params
from .stores_constants import DEFAULT_FILTERS, STORE_FILTERS, PER_PAGE
from .stores_service import StoreService

store = Blueprint('store', __name__)
logger = logging.getLogger('grubstack')

store_service = StoreService()
menu_service = MenuService()

@store.route('/stores', methods=['GET'])
@jwt_required()
@requires_permission("ViewStores")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = store_service.get_all(page, limit, generate_filters(STORE_FILTERS, request.args))

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve stores. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/stores', methods=['POST'])
@jwt_required()
@requires_permission("MaintainStores")
def create():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      name = params['name']
      store_type = params['store_type']

      count = store_service.get_store_count()
      limit = store_service.get_store_limit()

      if count >= limit and limit != -1:
        return gs_make_response(message='Unable to create store. Your subscription limit has been reached.',
                        status=GStatusCode.ERROR,
                        httpstatus=400)

      if name:
        store = store_service.search(name, store_type)

        if store is not None:
          return gs_make_response(message='That store and store type combination already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          store_service.create(format_params(params))
          store = store_service.search(name, store_type)

          if store is not None:
            headers = {'Location': url_for('store.get', store_id=store['id'])}
            return gs_make_response(message=f'Store {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=store)

          else:
            return gs_make_response(message='Unable to create store',
                            status=GStatusCode.ERROR,
                            httpstatus=500)
                            
      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create store',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/stores/<int:store_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewStores")
def get(store_id: int):
  try:
    store = store_service.get(store_id, DEFAULT_FILTERS)
    
    if store:
      return gs_make_response(data=store)

    else:
      return gs_make_response(message='Store not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/stores/<int:store_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainStores")
def delete(store_id: int):
  try:
    store = store_service.get(store_id)

    if store is None:
      return gs_make_response(message='Store not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

    else:
      qry = store_service.delete(store_id)
      return gs_make_response(message=f'Store #{store_id} deleted')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/stores', methods=['PUT'])
@jwt_required()
@requires_permission("MaintainStores")
def update():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      store_id = params['id']
      name = params['name']

      if store_id and name:
        row = store_service.get(store_id)

        if row is None:
          return gs_make_response(message=f'Store not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          store_service.update(store_id, format_params(params))
          headers = {'Location': url_for('store.get', store_id=store_id)}
          return gs_make_response(message=f'Store {name} successfully updated',
                    httpstatus=201,
                    headers=headers)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update store',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/stores/<int:store_id>/menus', methods=['GET'])
@jwt_required()
@requires_permission("MaintainStores")
def get_all_menus(store_id: int):
  try:
    store = store_service.get(store_id, DEFAULT_FILTERS)

    if store == None:
      return gs_make_response(message='Store not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
                              
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = store_service.get_menus_paginated(store_id, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve menus. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/stores/<int:store_id>/menus', methods=['POST'])
@jwt_required()
@requires_permission("MaintainStores")
def add_menu(store_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['menu_id']

      if store_id is not None and menu_id is not None:
        store = store_service.get(store_id)
        menu = menu_service.get(menu_id)

        is_existing = store_service.menu_exists(store_id, menu_id)
        
        if store is None:
          return gs_make_response(message='Store not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if menu is None:
          return gs_make_response(message='Menu not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          if not is_existing:
            store_service.add_menu(store_id, menu_id)
            
            return gs_make_response(message=f'Menu #{menu_id} added to store', httpstatus=201)
          else:
            return gs_make_response(message=f'Menu already exists on store',
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

@store.route('/stores/<int:store_id>/menus/<int:menu_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainStores")
def delete_menu(store_id: int, menu_id: int):
  try:
    is_existing = store_service.menu_exists(store_id, menu_id)

    if is_existing is None:
      return gs_make_response(message='Invalid store menu',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      store_service.delete_menu(store_id, menu_id)
      return gs_make_response(message=f'Menu #{menu_id} deleted from store')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(store, url_prefix=config.get('general', 'urlprefix', fallback='/'))
