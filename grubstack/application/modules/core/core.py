import logging, json, requests
from flask import Blueprint, url_for, request
from grubstack import app, config, gsprod
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, get_token_auth_header

core = Blueprint('core', __name__)
logger = logging.getLogger('grubstack')

@core.route('/core/versions', methods=['GET'])
def get_versions():
  try:
    json_data = []
    versions = gsprod.fetchall("SELECT * FROM gs_version")
    for version in versions:
      json_data.append({
        "id": version['pid'],
        "version": version['version']
      })
    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@core.route('/core/updateApps', methods=['POST'])
@requires_auth
def update_apps():
  try:
    products = gsprod.fetchall("SELECT app_id, app_url, c.tenant_id, c.product_id, p.is_front_end_app, p.product_name, p.product_description FROM gs_tenant_app c INNER JOIN gs_product p on p.product_id = c.product_id WHERE c.tenant_id = %s", (app.config['TENANT_ID'],))

    for product in products:
      if product['product_name'] != 'GrubStack API':
        url = 'https://api.grubstack.app/v1/product/app/restart'
        data = {"params": {"app_id": product['app_id']}}
        headers = {
          'Authorization': 'Bearer ' + get_token_auth_header(),
          'Content-Type': 'application/json'
        }
        resp = requests.post(url, json=data, headers=headers, verify=False)

    return gs_make_response(message='Apps updated successfully')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)


app.register_blueprint(core, url_prefix=config.get('general', 'urlprefix', fallback='/'))