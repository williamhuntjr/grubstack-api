import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission

from grubstack.application.utilities.request import verify_params
from grubstack.application.utilities.filters import generate_filters, create_pagination_params
from grubstack.application.modules.products.menus.menus_service import MenuService

from .locations_utilities import format_params
from .locations_constants import LOCATION_FILTERS, REQUIRED_FIELDS

from .locations_service import LocationService

location = Blueprint('location', __name__)
logger = logging.getLogger('grubstack')

location_service = LocationService()
menu_service = MenuService()

@location.route('/locations', methods=['GET'])
@jwt_required()
@requires_permission("ViewLocations")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)
    json_data, total_rows, total_pages = location_service.get_all(page, limit, generate_filters(LOCATION_FILTERS, request.args))

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve locations. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

# TODO: add required fields exception
@location.route('/locations', methods=['POST'])
@jwt_required()
@requires_permission("MaintainLocations")
def create():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      verify_params(params, REQUIRED_FIELDS)

      count = location_service.get_location_count()
      limit = location_service.get_location_limit()

      if count >= limit and limit != -1:
        return gs_make_response(message='Unable to create location. Your subscription limit has been reached.',
                        status=GStatusCode.ERROR,
                        httpstatus=400)

      name = params['name']
      location = location_service.search(name)

      if location is not None:
        return gs_make_response(message='That location already exists. Try a different name',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
      else:
        location_id = location_service.create(format_params(params))[0]
        location = location_service.get(location_id)

        headers = {'Location': url_for('location.get', location_id=location_id)}
        return gs_make_response(message='Location created successfully',
                              httpstatus=201,
                              headers=headers,
                              data=location)
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
    return gs_make_response(message='Unable to create location',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<int:location_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewLocations")
def get(location_id: int): 
  try:
    location = location_service.get(location_id, generate_filters(LOCATION_FILTERS, request.args))

    if location:
      return gs_make_response(data=location)

    else:
      return gs_make_response(message='Location not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error retrieving location',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<int:location_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainLocations")
def delete(location_id: int):
  try:
    location = location_service.get(location_id)

    if location is None:
      return gs_make_response(message='Location not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      qry = location_service.delete(location_id)
      return gs_make_response(message=f'Location #{location_id} deleted')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<int:location_id>', methods=['PATCH'])
@jwt_required()
@requires_permission("MaintainLocations")
def update(location_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      if location_id:
        location = location_service.get(location_id)

        if location is None:
          return gs_make_response(message='Location not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          if 'name' in params:
            location_search = location_service.search(params['name'])
            if location_search is not None and location_search['id'] != location_id:
              return gs_make_response(message='That location already exists. Try a different name',
                        status=GStatusCode.ERROR,
                        httpstatus=400)

          location_service.update(location_id, format_params(params, location))
          location = location_service.get(location_id)

          headers = {'Location': url_for('location.get', location_id=location['id'])}
          return gs_make_response(message=f'Location #{location_id} updated',
                                  httpstatus=201,
                                  headers=headers,
                                  data=location)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update location',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<int:location_id>/menus', methods=['GET'])
@jwt_required()
@requires_permission("ViewLocations")
def get_all_menus(location_id: int):
  try:
    location = location_service.get(location_id)

    if location == None:
      return gs_make_response(message='Location not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = location_service.get_menus_paginated(location_id, page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve location menus. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<int:location_id>/menus', methods=['POST'])
@jwt_required()
@requires_permission("MaintainLocations")
def add_menu(location_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      menu_id = params['menu_id']

      if location_id is not None and menu_id is not None:
        location = location_service.get(location_id)
        menu = menu_service.get(menu_id)

        is_existing = location_service.menu_exists(location_id, menu_id)
        
        if location is None:
          return gs_make_response(message='Location not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if menu is None:
          return gs_make_response(message='Menu not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          if not is_existing:
            location_service.add_menu(location_id, menu_id)
            
            return gs_make_response(message=f'Menu #{menu_id} added to location', httpstatus=201)
          else:
            return gs_make_response(message='Menu already exists on location',
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

@location.route('/locations/<int:location_id>/menus/<int:menu_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainLocations")
def delete_menu(location_id: int, menu_id: int):
  try:
    is_existing = location_service.menu_exists(location_id, menu_id)

    if is_existing is None:
      return gs_make_response(message='Location menu does not exist',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      location_service.delete_menu(location_id, menu_id)
      return gs_make_response(message=f'Menu #{menu_id} deleted from location')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(location, url_prefix=config.get('general', 'urlprefix', fallback='/'))
