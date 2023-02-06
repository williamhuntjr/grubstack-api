import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import AuthError, requires_auth, requires_permission, get_user_id

menu = Blueprint('menu', __name__)
logger = logging.getLogger('grubstack')
per_page = 10

@menu.route('/menus', methods=['GET'])
@requires_auth
@requires_permission("ViewMenus")
def get_all():
  try:
    json_data = []
    menus = gsdb.fetchall("SELECT * FROM gs_menu ORDER BY name ASC")
    
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = per_page
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    menus_list = []
    for menu in menus:
      menus_list.append({
        "id": menu['menu_id'],
        "name": menu['name'],
        "description": menu['description'],
        "thumbnail_url": menu['thumbnail_url']
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

@menu.route('/menu/create', methods=['POST'])
@requires_auth
@requires_permission("MaintainMenus")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      name = params['name']
      description = params['description'] 
      thumbnail_url = params['thumbnail_url']

      if name and description and thumbnail_url:
        # Check if exists
        row = gsdb.fetchall("SELECT * from gs_menu WHERE name = %s", (name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That menu already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("INSERT INTO gs_menu VALUES (%s, DEFAULT, %s, %s, %s)", (app.config["TENANT_ID"], name, description, thumbnail_url,))
          row = gsdb.fetchone("SELECT * FROM gs_menu WHERE name = %s", (name,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('menu.get', menu_id=row['menu_id'])}
            return gs_make_response(message=f'Menu {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=row)
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
@requires_auth
@requires_permission("ViewMenus")
def get(menu_id: int):
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)

      # Check if exists
      row = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menu_id,))
      if row: 
        json_data = {
          "id": row['menu_id'],
          "name": row['name'],
          "description": row['description'],
        }

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/delete', methods=['POST'])
@requires_auth
@requires_permission("MaintainMenus")
def delete():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['menu_id']

      if menu_id:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menu_id,))
        if row is None:
          return gs_make_response(message='Invalid menu',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_menu WHERE menu_id = %s", (menu_id,))
          qry = gsdb.execute("DELETE FROM gs_menu_item WHERE menu_id = %s", (menu_id,))
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
@requires_auth
@requires_permission("MaintainMenus")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['id']
      name = params['name']
      description = params['description'] 
      thumbnail_url = params['thumbnail_url']

      if menu_id and name and description and thumbnail_url:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menu_id,))

        if row is None:
          return gs_make_response(message=f'Menu {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_menu SET (name, description, thumbnail_url) = (%s, %s, %s) WHERE menu_id = %s", (name, description, thumbnail_url, menu_id,))
          headers = {'Location': url_for('menu.get', menu_id=menu_id)}
          return gs_make_response(message=f'Menu {name} successfully updated',
                    httpstatus=201,
                    headers=headers,
                    data=json_data)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update menu',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/<int:menuId>', methods=['GET'])
@requires_auth
@requires_permission("ViewMenus")
def get_menu(menuId):
  try:
    json_data = {}
    menu = gsdb.fetchone("""SELECT menu_id, name, description, thumbnail_url FROM gs_menu WHERE menu_id = %s""", (menuId,))
    if menu:
      json_data = {
        "id": menu['menu_id'],
        "name": menu['name'],
        "description": menu['description'],
        "thumbnail_url": menu['thumbnail_url'],
      }
      return gs_make_response(data=json_data)

    else:
      return gs_make_response(message='Invalid menu ID',
                              status=GStatusCode.ERROR,
                              httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve menu. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/<int:menuId>/items', methods=['GET'])
@requires_auth
@requires_permission("ViewMenus")
def get_all_items(menuId):
  try:
    json_data = []
    items = gsdb.fetchall("""SELECT c.item_id, name, description, thumbnail_url, price, sale_price, is_onsale
                                    FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                                    WHERE p.menu_id = %s ORDER BY name ASC""", (menuId,))
    
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = per_page
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    items_list = []
    for item in items:
      items_list.append({
        "id": item['item_id'],
        "name": item['name'],
        "description": item['description'],
        "thumbnail_url": item['thumbnail_url'],
        "price": item['price'],
        "sale_price": item['sale_price'],
        "is_onsale": item['is_onsale']
      })

    # Calculate paged data
    offset = page - 1
    start = offset * limit
    end = start + limit
    total_pages = ceil(len(items) / limit)

    # Get paged data
    json_data = items_list[start:end]

    return gs_make_response(data=json_data, totalrowcount=len(items), totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve items. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@menu.route('/menu/addItem', methods=['POST'])
@requires_auth
@requires_permission("MaintainMenus")
def add_item():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['menu_id']
      item_id = params['item_id']
      price = params['price'] if 'price' in params else 0
      sale_price = params['sale_price'] if 'sale_price' in params else 0
      is_onsale = params['is_onsale'] if 'is_onsale' in params else False

      if menu_id is not None and item_id is not None:
        # Check if exists
        menu = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menu_id,))
        item = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))
        is_existing = gsdb.fetchone("SELECT * FROM gs_menu_item WHERE menu_id = %s AND item_id = %s", (menu_id, item_id,))
        if menu is None or item is None:
          return gs_make_response(message='Invalid menu or invalid item',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          if not is_existing:
            qry = gsdb.execute("INSERT INTO gs_menu_item VALUES (%s, %s, %s, %s, %s, %s)", (app.config["TENANT_ID"], menu_id, item_id, price, sale_price, is_onsale,))
            return gs_make_response(message=f'Item #{item_id} added to menu')
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
@requires_auth
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
        # Check if exists
        menu = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menu_id,))
        menu_item = gsdb.fetchone("SELECT * FROM gs_menu_item WHERE menu_id = %s AND item_id = %s", (menu_id, item_id,))
        if menu is None or menu_item is None:
          return gs_make_response(message='Invalid menu or invalid item',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_menu_item WHERE menu_id = %s AND item_id = %s", (menu_id, item_id,))
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
@requires_auth
@requires_permission("MaintainMenus")
def update_item():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['menu_id']
      item_id = params['item_id']
      price = params['price']
      sale_price = params['sale_price']
      is_onsale = params['is_onsale']

      if menu_id is not None and item_id is not None and price is not None and sale_price is not None and is_onsale is not None:
        # Check if exists
        menu = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menu_id,))
        item = gsdb.fetchone("SELECT * FROM gs_item WHERE item_id = %s", (item_id,))
        is_existing = gsdb.fetchone("SELECT * FROM gs_menu_item WHERE menu_id = %s AND item_id = %s", (menu_id, item_id,))
        if menu is None or item is None:
          return gs_make_response(message='Invalid menu or invalid item',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          if is_existing:
            qry = gsdb.execute("UPDATE gs_menu_item SET price = %s, sale_price = %s, is_onsale = %s WHERE menu_id = %s AND item_id = %s", (price, sale_price, is_onsale, menu_id, item_id,))
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
