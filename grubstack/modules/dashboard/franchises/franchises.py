import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from grubstack import app, config, gsdb, gsprod
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission
from .franchises_utilities import formatFranchise, getFranchises, formatParams

franchise = Blueprint('franchise', __name__)
logger = logging.getLogger('grubstack')

PER_PAGE = app.config['PER_PAGE']

@franchise.route('/franchises', methods=['GET'])
@requires_auth
@requires_permission("ViewFranchises")
def get_all():
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)
    json_data, total_rows, total_pages = getFranchises(page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve franchises. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/create', methods=['POST'])
@requires_auth
@requires_permission("MaintainFranchises")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      name, description, thumbnail_url = formatParams(params)

      # Check if has open slots
      rows = gsdb.fetchall("SELECT * FROM gs_franchise")
      limit = gsprod.fetchone("SELECT franchise_count FROM gs_tenant_features WHERE tenant_id = %s", (app.config['TENANT_ID'],))
      if len(rows) >= limit[0]:
        return gs_make_response(message='Unable to create franchise. You are out of slots',
                        status=GStatusCode.ERROR,
                        httpstatus=401)

      if name:
        # Check if exists
        row = gsdb.fetchall("SELECT * FROM gs_franchise WHERE name = %s", (name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That franchise already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_franchise 
                                (tenant_id, franchise_id, name, description, thumbnail_url) 
                                VALUES 
                                (%s, DEFAULT, %s, %s, %s)""", (app.config["TENANT_ID"], name, description, thumbnail_url))
          row = gsdb.fetchone("SELECT * FROM gs_franchise WHERE name = %s", (name,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('franchise.get', franchise_id=row['franchise_id'])}
            return gs_make_response(message=f'Franchise {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=row)
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create franchise',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/<string:franchise_id>', methods=['GET'])
@requires_auth
@requires_permission("ViewFranchises")
def get(franchise_id: int):
  try:
    json_data = {}
    # Check if exists
    row = gsdb.fetchone("SELECT * FROM gs_franchise WHERE franchise_id = %s", (franchise_id,))
    if row:
      stores = gsdb.fetchall("""SELECT c.store_id, name, address1, city, state, postal, store_type, thumbnail_url, phone_number
                                FROM gs_store c INNER JOIN gs_franchise_store p ON p.store_id = c.store_id 
                                WHERE p.franchise_id = %s ORDER BY name ASC""", (franchise_id,))
      stores_list = []
      if stores != None:
        for store in stores:
          stores_list.append({
            "id": store['store_id'],
            "name": store['name'],
            "address1": store['address1'],
            "city": store['city'],
            "state": store['state'],
            "postal": store['postal'],
            "store_type": store['store_type'],
            "thumbnail_url": store['thumbnail_url'],
            "phone_number": store['phone_number'],
          })
      json_data = formatFranchise(row, stores_list)

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/delete', methods=['POST'])
@requires_auth
@requires_permission("MaintainFranchises")
def delete():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      franchise_id = params['franchise_id']
      if franchise_id:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_franchise WHERE franchise_id = %s", (franchise_id,))
        if row is None:
          return gs_make_response(message='Invalid franchise',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_franchise WHERE franchise_id = %s", (franchise_id,))
          return gs_make_response(message=f'Franchise #{franchise_id} deleted')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/update', methods=['POST'])
@requires_auth
@requires_permission("MaintainFranchises")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      franchise_id = params['id']
      name, description, thumbnail_url = formatParams(params)

      if franchise_id and name:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_franchise WHERE franchise_id = %s", (franchise_id,))

        if row is None:
          return gs_make_response(message=f'Franchise {name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("UPDATE gs_franchise SET (name, description, thumbnail_url) = (%s, %s, %s) WHERE franchise_id = %s", (name, description, thumbnail_url, franchise_id,))
          headers = {'Location': url_for('franchise.get', franchise_id=franchise_id)}
          return gs_make_response(message=f'Franchise {name} successfully updated',
                    httpstatus=201,
                    headers=headers,
                    data=json_data)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update franchise',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/<int:franchiseId>/stores', methods=['GET'])
@requires_auth
@requires_permission("MaintainFranchises")
def get_all_stores(franchiseId):
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    json_data, total_rows, total_pages = getFranchiseStores(franchiseId, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve stores. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/addStore', methods=['POST'])
@requires_auth
@requires_permission("MaintainFranchises")
def add_store():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      franchise_id = params['franchise_id']
      store_id = params['store_id']

      if franchise_id is not None and store_id is not None:
        # Check if exists
        franchise = gsdb.fetchone("SELECT * FROM gs_franchise WHERE franchise_id = %s", (franchise_id,))
        store = gsdb.fetchone("SELECT * FROM gs_store WHERE store_id = %s", (store_id,))
        is_existing = gsdb.fetchone("SELECT * FROM gs_franchise_store WHERE franchise_id = %s AND store_id = %s", (franchise_id, store_id,))
        if franchise is None or store is None:
          return gs_make_response(message='Invalid franchise or invalid store',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          if not is_existing:
            qry = gsdb.execute("""INSERT INTO gs_franchise_store 
                                  (tenant_id, franchise_id, store_id)
                                  VALUES 
                                  (%s, %s, %s)""", (app.config["TENANT_ID"], franchise_id, store_id,))
            return gs_make_response(message=f'Store #{store_id} added to franchise')
          else:
            return gs_make_response(message=f'Store already exists on franchise',
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

@franchise.route('/franchise/deleteStore', methods=['POST'])
@requires_auth
@requires_permission("MaintainFranchises")
def delete_store():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      franchise_id = params['franchise_id']
      store_id = params['store_id']

      if franchise_id and store_id:
        # Check if exists
        franchise_store = gsdb.fetchone("SELECT * FROM gs_franchise_store WHERE franchise_id = %s AND store_id = %s", (franchise_id, store_id,))
        if franchise_store is None:
          return gs_make_response(message='Invalid franchise store',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_franchise_store WHERE franchise_id = %s AND store_id = %s", (franchise_id, store_id,))
          return gs_make_response(message=f'Store #{store_id} deleted from franchise')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(franchise, url_prefix=config.get('general', 'urlprefix', fallback='/'))