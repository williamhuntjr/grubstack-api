import logging, json

from math import ceil
from flask import Blueprint, url_for, request

from grubstack import app, config, gsdb, gsprod
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission
from grubstack.application.utilities.filters import generate_filters, create_pagination_params
from grubstack.application.modules.stores.stores_service import StoreService

from .franchises_utilities import format_params
from .franchises_constants import DEFAULT_FILTERS, FRANCHISE_FILTERS, PER_PAGE
from .franchises_service import FranchiseService

franchise = Blueprint('franchise', __name__)
logger = logging.getLogger('grubstack')

franchise_service = FranchiseService()
store_service = StoreService()

@franchise.route('/franchises', methods=['GET'])
@jwt_required()
@requires_permission("ViewFranchises")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = franchise_service.get_all(page, limit, generate_filters(FRANCHISE_FILTERS, request.args))

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve franchises. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/create', methods=['POST'])
@jwt_required()
@requires_permission("MaintainFranchises")
def create():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      name = params['name']

      count = franchise_service.get_franchise_count()
      limit = franchise_service.get_franchise_limit()

      if count >= limit:
        return gs_make_response(message='Unable to create franchise. Your subscription limit has been reached.',
                        status=GStatusCode.ERROR,
                        httpstatus=401)

      if name:
        franchise = franchise_service.search(name)

        if franchise:
          return gs_make_response(message='That franchise already exists. Try a different name',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          franchise_service.create(format_params(params))
          franchise = franchise_service.search(name)

          if franchise is not None:
            headers = {'Location': url_for('franchise.get', franchise_id=franchise['id'])}
            return gs_make_response(message=f'Franchise {name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=franchise)
          else:
            return gs_make_response(message='Unable to create franchise',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create franchise',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/<int:franchise_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewFranchises")
def get(franchise_id: int):
  try:
    franchise = franchise_service.get(franchise_id, DEFAULT_FILTERS)

    if franchise:
      return gs_make_response(data=franchise)

    else:
      return gs_make_response(message='Franchise not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/delete', methods=['POST'])
@jwt_required()
@requires_permission("MaintainFranchises")
def delete():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      franchise_id = params['franchise_id']

      if franchise_id:
        franchise = franchise_service.get(franchise_id)
        if franchise is None:
          return gs_make_response(message='Franchise not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          franchise_service.delete(franchise_id)
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
@jwt_required()
@requires_permission("MaintainFranchises")
def update():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      franchise_id = params['id']
      name = params['name']

      if franchise_id and name:
        franchise = franchise_service.get(franchise_id)

        if franchise is None:
          return gs_make_response(message=f'Franchise not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          franchise_service.update(franchise_id, format_params(params))
          headers = {'Location': url_for('franchise.get', franchise_id=franchise_id)}
          return gs_make_response(message=f'Franchise {name} successfully updated',
                    httpstatus=201,
                    headers=headers)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update franchise',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/<int:franchise_id>/stores', methods=['GET'])
@jwt_required()
@requires_permission("MaintainFranchises")
def get_all_stores(franchise_id: int):
  try:
    franchise = franchise_service.get(franchise_id, DEFAULT_FILTERS)

    if franchise == None:
      return gs_make_response(message='Franchise not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = franchise_service.get_stores_paginated(franchise_id, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve stores. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@franchise.route('/franchise/addStore', methods=['POST'])
@jwt_required()
@requires_permission("MaintainFranchises")
def add_store():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      franchise_id = params['franchise_id']
      store_id = params['store_id']

      if franchise_id is not None and store_id is not None:
        franchise = franchise_service.get(franchise_id)
        store = store_service.get(store_id)

        is_existing = franchise_service.store_exists(franchise_id, store_id)
        
        if franchise is None:
          return gs_make_response(message='Franchise not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)

        if store is None:
          return gs_make_response(message='Store not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)

        else:
          if not is_existing:
            franchise_service.add_store(franchise_id, store_id)
            return gs_make_response(message=f'Store #{store_id} added to franchise', httpstatus=201)

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
@jwt_required()
@requires_permission("MaintainFranchises")
def delete_store():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      franchise_id = params['franchise_id']
      store_id = params['store_id']

      if franchise_id and store_id:
        is_existing = franchise_service.store_exists(franchise_id, store_id)

        if is_existing is None:
          return gs_make_response(message='Invalid franchise store',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          franchise_service.delete_store(franchise_id, store_id)
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
