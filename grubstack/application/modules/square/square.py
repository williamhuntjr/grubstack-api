import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.authentication import jwt_required, requires_permission

from .square_service import SquareService

square = Blueprint('square', __name__)
logger = logging.getLogger('grubstack')

square_service = SquareService()

@square.route('/square/locations', methods=['GET'])
@jwt_required()
@requires_permission("ViewLocations", "MaintainLocations")
def get_all():
  try:
    json_data = square_service.get_locations()
    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve square locations. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(square, url_prefix=config.get('general', 'urlprefix', fallback='/'))
