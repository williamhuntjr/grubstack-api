import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission, get_user_id

store = Blueprint('store', __name__)
logger = logging.getLogger('grubstack')
per_page = 10

@store.route('/stores', methods=['GET'])
@requires_auth
@requires_permission("ViewStores")
def get_all():
  try:
    json_data = []
    stores = gsdb.fetchall("SELECT * FROM gs_store ORDER BY name ASC")
    
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = per_page
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    stores_list = []
    for store in stores:
      menus = gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url
                                FROM gs_menu c INNER JOIN gs_store_menu p ON p.menu_id = c.menu_id 
                                WHERE p.store_id = %s ORDER BY name ASC""", (store['store_id'],))
      menus_list = []
      if menus != None:
        for menu in menus:
          menus_list.append({
            "id": menu['menu_id'],
            "name": menu['name'],
            "description": menu['description'],
            "thumbnail_url": menu['thumbnail_url'],
          })

      stores_list.append({
        "id": store['store_id'],
        "name": store['name'],
        "address1": store['address1'],
        "city": store['city'],
        "state": store['state'],
        "postal": store['postal'],
        "store_type": store['store_type'],
        "thumbnail_url": store['thumbnail_url'],
        "menus": menus_list
      })

    # Calculate paged data
    offset = page - 1
    start = offset * limit
    end = start + limit
    total_pages = ceil(len(stores) / limit)

    # Get paged data
    json_data = stores_list[start:end]

    return gs_make_response(data=json_data, totalrowcount=len(stores), totalpages=total_pages)

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
      name = params['name']
      address1 = params['address1'] 
      city = params['city'] 
      state = params['state'] 
      postal = params['postal'] 
      store_type = params['store_type'] 
      thumbnail_url = params['thumbnail_url'] 

      if name and address1 and city and state and postal and store_type and thumbnail_url:
        # Check if exists
        row = gsdb.fetchall("SELECT * FROM gs_store WHERE name = %s AND store_type = %s ORDER BY name ASC", (get_user_id(), name, store_type,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That store and store type combination already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("INSERT INTO gs_store VALUES (%s, DEFAULT, %s, %s, %s, %s, %s, %s, %s)", (app.config["TENANT_ID"], name, address1, city, state, postal, store_type, thumbnail_url))
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
    json_data = {}
    # Check if exists
    row = gsdb.fetchone("SELECT * FROM gs_store WHERE store_id = %s", (store_id,))
    if row: 
      menus = gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url
                              FROM gs_menu c INNER JOIN gs_store_menu p ON p.menu_id = c.menu_id 
                              WHERE p.store_id = %s ORDER BY name ASC""", (store_id,))
      menus_list = []

      if menus != None:
        for menu in menus:
          menus_list.append({
            "id": menu['menu_id'],
            "name": menu['name'],
            "description": menu['description'],
            "thumbnail_url": menu['thumbnail_url'],
          })

      json_data = {
        "id": row['store_id'],
        "name": row['name'],
        "address1": row['address1'],
        "city": row['city'],
        "state": row['state'],
        "postal": row['postal'],
        "store_type": row['store_type'],
        "thumbnail_url": row['thumbnail_url'],
        "menus": menus_list
      }

    return gs_make_response(data=json_data)

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
        row = gsdb.fetchone("SELECT * FROM gs_store WHERE store_id = %s", (store_id,))
        if row is None:
          return gs_make_response(message='Invalid store',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_store WHERE store_id = %s", (store_id,))
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
      name = params['name']
      address1 = params['address1'] 
      city = params['city'] 
      state = params['state'] 
      postal = params['postal'] 
      store_type = params['store_type'] 
      thumbnail_url = params['thumbnail_url'] 

      if store_id and name and address1 and city and state and postal and store_type and thumbnail_url:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_store WHERE store_id = %s", (store_id,))

        if row is None:
          return gs_make_response(message=f'Store {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_store SET (name, address1, city, state, postal, store_type, thumbnail_url) = (%s, %s, %s, %s, %s, %s, %s) WHERE store_id = %s", (name, address1, city, state, postal, store_type, thumbnail_url, store_id,))
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
    json_data = []
    menus = gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url
                            FROM gs_menu c INNER JOIN gs_store_menu p ON p.menu_id = c.menu_id 
                            WHERE p.store_id = %s ORDER BY name ASC""", (storeId,))

    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = per_page
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    menus_list = []
    if menus != None:
      for menu in menus:
        menus_list.append({
          "id": menu['menu_id'],
          "name": menu['name'],
          "description": menu['description'],
          "thumbnail_url": menu['thumbnail_url'],
        })

    # Calculate paged data
    offset = page - 1
    start = offset * limit
    end = start + limit
    total_pages = ceil(len(menus) / limit)

    # Get paged data
    json_data = menus_list[start:end]

    return gs_make_response(data=json_data, totalrowcount=len(menus), totalpages=total_pages)

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
        store = gsdb.fetchone("SELECT * FROM gs_store WHERE store_id = %s", (store_id,))
        menu = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menu_id,))
        is_existing = gsdb.fetchone("SELECT * FROM gs_store_menu WHERE store_id = %s AND menu_id = %s", (store_id, menu_id,))
        if store is None or menu is None:
          return gs_make_response(message='Invalid store or invalid menu',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          if not is_existing:
            qry = gsdb.execute("INSERT INTO gs_store_menu VALUES (%s, %s, %s)", (app.config["TENANT_ID"], store_id, menu_id,))
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
