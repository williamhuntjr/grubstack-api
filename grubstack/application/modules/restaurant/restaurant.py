import logging, json

from flask import Blueprint, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission

from .restaurant_service import RestaurantService

restaurant = Blueprint('restaurant', __name__)
logger = logging.getLogger('grubstack')

restaurant_service = RestaurantService()

@restaurant.route('/restaurant/properties', methods=['GET'])
@jwt_required()
@requires_permission('ViewRestaurant')
def get_all_properties():
  try:
    properties = restaurant_service.get_all_properties()

    return gs_make_response(data=properties)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve restaurant properties. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@restaurant.route('/restaurant/properties/<string:property_key>', methods=['GET'])
@jwt_required()
@requires_permission('ViewRestaurant')
def get_property(property_key: str):
  try:
    is_existing = restaurant_service.property_exists(property_key)

    if is_existing is False:
      return gs_make_response(data={ "key": property_key, "value": None })

    else:
      property_info = restaurant_service.get_property(property_key)
      return gs_make_response(data=property_info)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve property. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@restaurant.route('/restaurant/properties', methods=['PUT'])
@jwt_required()
@requires_permission('MaintainRestaurant')
def update_property():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      if 'key' in params and 'value' in params:
        key = params['key']
        value = params['value']

        restaurant_service.update_property(key, value)
        return gs_make_response(data={"key": key, "value": value}, message='Property updated successfully', httpstatus=201)

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

app.register_blueprint(restaurant, url_prefix=config.get('general', 'urlprefix', fallback='/'))