import logging

from flask import Blueprint, request
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_token
from grubstack.modules.dashboard.stores.stores_utilities import getStores

web = Blueprint('web', __name__)
logger = logging.getLogger('grubstack')

@web.route('/web/stores', methods=['GET'])
@requires_token
def get_stores():
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)
    json_data, total_rows, total_pages = getStores(page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve stores. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(web, url_prefix=config.get('general', 'urlprefix', fallback='/'))
