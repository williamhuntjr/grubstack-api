import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb, gsprod
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission
from grubstack.application.utilities.database import deleteStore
from grubstack.application.utilities.filters import generateFilters
from grubstack.application.modules.products.menus.menus_utilities import formatMenu
from .stores_utilities import formatStore, getStores, formatParams, getStore

store = Blueprint('store', __name__)
logger = logging.getLogger('grubstack')

PER_PAGE = app.config['PER_PAGE']
STORE_FILTERS = ['showMenus', 'showItems']

@store.route('/stores', methods=['GET'])
@requires_auth
@requires_permission("ViewStores")
def get_all():
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    json_data, total_rows, total_pages = getStores(page, limit, generateFilters(STORE_FILTERS, request.args))

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve stores. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/store/create', methods=['POST'])
@requires_auth
@requires_permission("MaintainStores")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      name, address1, city, state, postal, store_type, thumbnail_url, phone_number = formatParams(params)

      # Check if has open slots
      row = gsdb.fetchone("SELECT COUNT(*) FROM gs_store")
      limit = gsprod.fetchone("SELECT store_count FROM gs_tenant_features WHERE tenant_id = %s", (app.config['TENANT_ID'],))
      if row[0] >= limit[0]:
        return gs_make_response(message='Unable to create store. You are out of slots',
                        status=GStatusCode.ERROR,
                        httpstatus=401)

      if name:
        # Check if exists
        row = gsdb.fetchall("SELECT * FROM gs_store WHERE name = %s AND store_type = %s ORDER BY name ASC", (name, store_type,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That store and store type combination already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_store 
                                (tenant_id, store_id, name, address1, city, state, postal, store_type, thumbnail_url, phone_number) 
                                VALUES 
                                (%s, DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s)""", (app.config["TENANT_ID"], name, address1, city, state, postal, store_type, thumbnail_url, phone_number))
          row = gsdb.fetchone("SELECT * FROM gs_store WHERE name = %s AND store_type = %s", (name, store_type,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('store.get', store_id=row['store_id'])}
            return gs_make_response(message=f'Store {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=row)
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create store',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/store/<string:store_id>', methods=['GET'])
@requires_auth
@requires_permission("ViewStores")
def get(store_id: int):
  try:
    filters = {
      "showMenus": True,
      "showItems": True
    }
    store = getStore(store_id, filters)
    
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

@store.route('/store/delete', methods=['POST'])
@requires_auth
@requires_permission("MaintainStores")
def delete():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      store_id = params['store_id']

      if store_id:
        # Check if exists
        store = getStore(store_id)

        if store is None:
          return gs_make_response(message='Store not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = deleteStore(store_id)
          return gs_make_response(message=f'Store #{store_id} deleted')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/store/update', methods=['POST'])
@requires_auth
@requires_permission("MaintainStores")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      store_id = params['id']
      name, address1, city, state, postal, store_type, thumbnail_url, phone_number = formatParams(params)

      if store_id and name:
        # Check if exists
        row = getStore(store_id)

        if row is None:
          return gs_make_response(message=f'Store {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_store SET (name, address1, city, state, postal, store_type, thumbnail_url, phone_number) = (%s, %s, %s, %s, %s, %s, %s, %s) WHERE store_id = %s", (name, address1, city, state, postal, store_type, thumbnail_url, phone_number, store_id,))
          headers = {'Location': url_for('store.get', store_id=store_id)}
          return gs_make_response(message=f'Store {name} successfully updated',
                    httpstatus=201,
                    headers=headers,
                    data=json_data)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update store',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/store/<int:storeId>/menus', methods=['GET'])
@requires_auth
@requires_permission("MaintainStores")
def get_all_menus(storeId):
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    json_data, total_rows, total_pages = getStoreMenusPaginated(storeId, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve menus. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@store.route('/store/addMenu', methods=['POST'])
@requires_auth
@requires_permission("MaintainStores")
def add_menu():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      store_id = params['store_id']
      menu_id = params['menu_id']

      if store_id is not None and menu_id is not None:
        # Check if exists
        store = getStore(store_id)
        menu = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menu_id,))
        is_existing = gsdb.fetchone("SELECT * FROM gs_store_menu WHERE store_id = %s AND menu_id = %s", (store_id, menu_id,))
        if store is None or menu is None:
          return gs_make_response(message='Invalid store or invalid menu',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          if not is_existing:
            qry = gsdb.execute("""INSERT INTO gs_store_menu 
                                  (tenant_id, store_id, menu_id)
                                  VALUES 
                                  (%s, %s, %s)""", (app.config["TENANT_ID"], store_id, menu_id,))
            return gs_make_response(message=f'Menu #{menu_id} added to store')
          else:
            return gs_make_response(message=f'Menu already exists on store',
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

@store.route('/store/deleteMenu', methods=['POST'])
@requires_auth
@requires_permission("MaintainStores")
def delete_menu():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      store_id = params['store_id']
      menu_id = params['menu_id']

      if store_id and menu_id:
        # Check if exists
        store_menu = gsdb.fetchone("SELECT * FROM gs_store_menu WHERE store_id = %s AND menu_id = %s", (store_id, menu_id,))
        if store_menu is None:
          return gs_make_response(message='Invalid store menu',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_store_menu WHERE store_id = %s AND menu_id = %s", (store_id, menu_id,))
          return gs_make_response(message=f'Menu #{menu_id} deleted from store')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(store, url_prefix=config.get('general', 'urlprefix', fallback='/'))