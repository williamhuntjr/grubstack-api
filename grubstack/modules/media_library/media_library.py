import logging
from flask import Blueprint

from grubstack import app, config

from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth

media_library = Blueprint('media_library', __name__)
logger = logging.getLogger('grubstack')

@media_library.route('/media-library', methods=['GET'])
@requires_auth
def get_all():
  return gs_make_response(data=[])

app.register_blueprint(media_library, url_prefix=config.get('general', 'urlprefix', fallback='/'))
