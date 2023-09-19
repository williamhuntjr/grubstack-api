import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import AuthError, requires_auth, requires_permission
from .menus_utilities import formatMenu, getMenus, formatParams, getMenuItems

menu = Blueprint('menu', __name__)
logger = logging.getLogger('grubstack')

PER_PAGE = app.config['PER_PAGE']

@menu.route('/menus', methods=['GET'])
@requires_auth
@requires_permission("ViewMenus")
def get_all():
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    json_data, total_rows, total_pages = getMenus(page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

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
      name, description, thumbnail_url, label_color = formatParams(params)

      if name:
        # Check if exists
        row = gsdb.fetchall("SELECT * from gs_menu WHERE name = %s", (name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That menu already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_menu 
                                (tenant_id, menu_id, name, description, thumbnail_url, label_color)
                                VALUES
                                (%s, DEFAULT, %s, %s, %s, %s)""", (app.config["TENANT_ID"], name, description, thumbnail_url, label_color,))
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

@menu.route('/menu/<string:menuId>', methods=['GET'])
@requires_auth
@requires_permission("ViewMenus")
def get(menuId: int):
  try:
    # Check if exists
    row = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menuId,))
    if row: 
      items = gsdb.fetchall("""SELECT c.item_id, name, description, thumbnail_url, label_color, price, sale_price, is_onsale
                                FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                                WHERE p.menu_id = %s ORDER BY name ASC""", (menuId,))
      items_list = []
      for item in items:
        items_list.append({
          "id": item['item_id'],
          "name": item['name'],
          "description": item['description'],
          "thumbnail_url": item['thumbnail_url'],
          "label_color": item['label_color'],
          "price": item['price'],
          "sale_price": item['sale_price'],
          "is_onsale": item['is_onsale']
        })
      json_data = formatMenu(row, items_list)

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
      name, description, thumbnail_url, label_color = formatParams(params)

      if menu_id and name and description and thumbnail_url:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_menu WHERE menu_id = %s", (menu_id,))

        if row is None:
          return gs_make_response(message=f'Menu {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_menu SET (name, description, thumbnail_url, label_color) = (%s, %s, %s, %s) WHERE menu_id = %s", (name, description, thumbnail_url, label_color, menu_id,))
          headers = {'Location': url_for('menu.get', menuId=menu_id)}
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

@menu.route('/menu/<int:menuId>/items', methods=['GET'])
@requires_auth
@requires_permission("ViewMenus")
def get_all_items(menuId):
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    json_data, total_rows, total_pages = getMenuItems(menuId, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

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
            qry = gsdb.execute("""INSERT INTO gs_menu_item 
                                  (tenant_id, menu_id, item_id, price, sale_price, is_onsale)
                                  VALUES 
                                  (%s, %s, %s, %s, %s, %s)""", (app.config["TENANT_ID"], menu_id, item_id, price, sale_price, is_onsale,))
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
