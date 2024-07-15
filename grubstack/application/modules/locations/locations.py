import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission, requires_all_permissions

from grubstack.application.utilities.request import verify_params
from grubstack.application.utilities.filters import generate_filters, create_pagination_params
from grubstack.application.modules.products.menus.menus_service import MenuService
from grubstack.application.modules.restaurant.restaurant_service import RestaurantService

from .locations_utilities import format_params, format_work_hour_params
from .locations_constants import LOCATION_FILTERS, REQUIRED_FIELDS, REQUIRED_WORK_HOUR_FIELDS

from .locations_service import LocationService

location = Blueprint('location', __name__)
logger = logging.getLogger('grubstack')

location_service = LocationService()
menu_service = MenuService()
restaurant_service = RestaurantService()

@location.route('/locations', methods=['GET'])
@jwt_required()
@requires_permission("ViewLocations", "MaintainLocations")
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
        location_service.initialize_work_hours(location_id)
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
@requires_permission("ViewLocations", "MaintainLocations")
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
@requires_permission("ViewLocations", "MaintainLocations")
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
@requires_all_permissions("MaintainLocations", "MaintainRestaurants")
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
@requires_all_permissions("MaintainLocations", "MaintainRestaurants")
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

@location.route('/locations/<int:location_id>/order-types', methods=['GET'])
@jwt_required()
@requires_permission("ViewLocations", "MaintainLocations", "ViewRestaurants", "MaintainRestaurants")
def get_order_types(location_id: int):
  try:
    order_types = location_service.get_order_types(location_id)
    return gs_make_response(data=order_types)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve order types for location.',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<int:location_id>/order-types/<int:order_type_id>', methods=['DELETE'])
@jwt_required()
@requires_all_permissions("MaintainLocations", "MaintainRestaurants")
def delete_order_type(location_id: int, order_type_id: int):
  try:
    is_existing = location_service.order_type_exists(location_id, order_type_id)

    if is_existing is None:
      return gs_make_response(message='Location order type does not exist',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      location_service.delete_order_type(location_id, order_type_id)
      return gs_make_response(message=f'Order type #{order_type_id} deleted from location')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<int:location_id>/order-types', methods=['POST'])
@jwt_required()
@requires_all_permissions("MaintainLocations", "MaintainRestaurants")
def add_order_type(location_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      order_type_id = params['order_type_id']

      if location_id is not None and order_type_id is not None:
        location = location_service.get(location_id)
        order_type = restaurant_service.get_order_type(order_type_id)

        is_existing = location_service.order_type_exists(location_id, order_type_id)
        
        if location is None:
          return gs_make_response(message='Location not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        if order_type is None:
          return gs_make_response(message='Order type not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          if not is_existing:
            location_service.add_order_type(location_id, order_type_id)
            
            return gs_make_response(message=f'Order type #{order_type_id} added to location', httpstatus=201)
          else:
            return gs_make_response(message='Order type already exists on location',
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

@location.route('/locations/<int:location_id>/working-hours/<int:working_hour_type_id>', methods=['PUT'])
@jwt_required()
@requires_all_permissions("MaintainLocations", "MaintainRestaurants")
def update_work_hour(location_id: int, working_hour_type_id: str):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      verify_params(params, REQUIRED_WORK_HOUR_FIELDS)

      location = location_service.get(location_id)
      hour_type = restaurant_service.get_working_hour_type(working_hour_type_id)

      if location is None:
        return gs_make_response(message='Location not found',
                                status=GStatusCode.ERROR,
                                httpstatus=404)
      if hour_type is None:
        return gs_make_response(message='Working Hour type not found',
                        status=GStatusCode.ERROR,
                        httpstatus=404)
      else:
        location_service.update_work_hour(location_id, working_hour_type_id, format_work_hour_params(params))
        return gs_make_response(message='Location work hour updated', httpstatus=204)
  except ValueError as e:
    return gs_make_response(message=e,
                            status=GStatusCode.ERROR,
                            httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<int:location_id>/working-hours', methods=['GET'])
@jwt_required()
@requires_permission("ViewLocations", "MaintainLocations", "ViewRestaurants", "MaintainRestaurants")
def get_work_hours(location_id: int):
  try:
    location = location_service.get(location_id)

    if location is None:
      return gs_make_response(message='Location not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      work_hours = location_service.get_work_hours(location_id)
      return gs_make_response(data=work_hours)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<int:location_id>/properties', methods=['GET'])
@jwt_required()
@requires_permission("ViewLocations", "MaintainLocations", "ViewRestaurants", "MaintainRestaurants")
def get_all_properties(location_id: int):
  try:
    location = location_service.get(location_id)

    if location is None:
      return gs_make_response(message='Location not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

    properties = location_service.get_all_properties(location_id)

    return gs_make_response(data=properties)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve restaurant properties. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<string:location_id>/properties/<string:property_key>', methods=['GET'])
@jwt_required()
@requires_permission("ViewLocations", "MaintainLocations", "ViewRestaurants", "MaintainRestaurants")
def get_property(location_id: str, property_key: str):
  try:
    location = location_service.get(location_id)

    if location is None:
      return gs_make_response(message='Location not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

    is_existing = location_service.property_exists(location_id, property_key)

    if is_existing is False:
      return gs_make_response(data={ "key": property_key, "value": None })

    else:
      property_info = location_service.get_property(location_id, property_key)
      return gs_make_response(data=property_info)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve property. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@location.route('/locations/<string:location_id>/properties', methods=['PUT'])
@jwt_required()
@requires_all_permissions("MaintainLocations", "MaintainRestaurants")
def update_property(location_id: str):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      location = location_service.get(location_id)

      if location is None:
        return gs_make_response(message='Location not found',
                                status=GStatusCode.ERROR,
                                httpstatus=404)

      if 'key' in params and 'value' in params:
        key = params['key']
        value = params['value']

        location_service.update_property(location_id, key, value)
        return gs_make_response(data={"location_id": location_id, "key": key, "value": value}, message='Property updated successfully', httpstatus=201)

      else:
        return gs_make_response(message='Invalid request',
                        status=GStatusCode.ERROR,
                        httpstatus=400)

    else:
      return gs_make_response(message='Invalid request',
                              status=GStatusCode.ERROR,
                              httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update property. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(location, url_prefix=config.get('general', 'urlprefix', fallback='/'))
