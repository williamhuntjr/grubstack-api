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

@restaurant.route('/restaurant/order-types', methods=['GET'])
@jwt_required()
def get_order_types():
  try:
    order_types = restaurant_service.get_order_types()
    return gs_make_response(data=order_types)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve Order types. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@restaurant.route('/restaurant/working-hour-types', methods=['GET'])
@jwt_required()
def get_working_hour_types():
  try:
    working_hour_types = restaurant_service.get_working_hour_types()
    return gs_make_response(data=working_hour_types)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve Working Hour types. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(restaurant, url_prefix=config.get('general', 'urlprefix', fallback='/'))