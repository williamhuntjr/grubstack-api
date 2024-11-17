import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.authentication import jwt_required, requires_permission
from grubstack.envelope import GStatusCode

from grubstack.application.modules.locations.locations_service import LocationService
from grubstack.application.modules.restaurant.restaurant_service import RestaurantService

from .orders_service import OrderService, ValidationError

orders = Blueprint('orders', __name__)
logger = logging.getLogger('grubstack')

location_service = LocationService()
restaurant_service = RestaurantService()
order_service = OrderService()

@orders.route('/orders/validate/<int:location_id>', methods=['POST'])
@jwt_required()
def validate(location_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      if 'items' not in data and 'order_type' not in data:
        return gs_make_response(message='Unable to validate order. Please include items and an order type.',
                        status=GStatusCode.ERROR,
                        httpstatus=400)
      else:
        items = data['items']
        order_type_exists = restaurant_service.order_type_exists(data['order_type'])
        if order_type_exists is False:
          return gs_make_response(message='Unable to validate order. Invalid order type.',
                        status=GStatusCode.ERROR,
                        httpstatus=400)
        else:
          order_type = restaurant_service.search_order_type(data['order_type'])
          location_order_type_exists = location_service.order_type_exists(location_id, order_type['id'])
          if location_order_type_exists is False:
            return gs_make_response(message='Unable to validate order. The specified Order Type does not exist on location.',
              status=GStatusCode.ERROR,
              httpstatus=400)
          else:
            is_open = location_service.verify_is_open(location_id, order_type['working_hour_type_id'])
            if is_open is False:
              return gs_make_response(message='Unable to validate order. The location is not accepting orders for the specified order type.',
                status=GStatusCode.ERROR,
                httpstatus=400)
            else:
              try:
                order_service.validate_cart(location_id, data['items'])
              except ValidationError as e:
                print(e)

  except:
    logger.exception(e)
    return gs_make_response(message='Unable to validate order. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(orders, url_prefix=config.get('general', 'urlprefix', fallback='/'))
