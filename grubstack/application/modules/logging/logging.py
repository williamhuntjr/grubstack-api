import logging

from flask import Blueprint, send_file

from grubstack import app, config

from grubstack.authentication import jwt_required, requires_permission

logs = Blueprint('logging', __name__)
logger = logging.getLogger('grubstack')

@logs.route('/logging/view/error-log', methods=['GET'])
@jwt_required()
@requires_permission("ViewLogging", "MaintainLogging")
def get_log():
  try:
    return send_file("/var/log/nginx/error.log")
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve log. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(logs, url_prefix=config.get('general', 'urlprefix', fallback='/'))