import json, requests, time
from datetime import datetime

from six.moves.urllib.request import urlopen

from functools import wraps
from jose import jwt

from pypika import Table, Query, Parameter

from flask import request, _request_ctx_stack, Blueprint, Response, jsonify, make_response
from flask_jwt_extended import (
  verify_jwt_in_request,
  create_access_token,
  get_current_user,
  get_jwt_identity,
  get_jwt,
  decode_token,
  unset_jwt_cookies,
  set_access_cookies,
  set_refresh_cookies
)

from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.user import GSUser

from . import app, config, logger, gsprod, gsdb, jwt

authentication = Blueprint('auth', __name__)

class AuthError(Exception):
  def __init__(self, error, status_code):
    self.error = error
    self.status_code = status_code

def epoch_to_datetime(epoch: int) -> datetime:
  return datetime.fromtimestamp(epoch)

def add_token_to_database(encoded_token: str, identity_claim: str, username: str) -> None:
  decoded_token = decode_token(encoded_token)
  jti = decoded_token['jti']
  token_type = decoded_token['type']
  user_identity = decoded_token[identity_claim]
  expires = epoch_to_datetime(decoded_token['exp'])
  revoked = False

  gs_jwt = Table('gs_jwt')

  qry = Query.into(gs_jwt).columns(
    'jwt_jti',
    'jwt_token_type',
    'jwt_token',
    'jwt_user_identity',
    'jwt_revoked',
    'jwt_expires',
    'jwt_username'
  ).insert(
    jti,
    token_type,
    encoded_token,
    user_identity,
    revoked,
    expires,
    username
  )

  gsprod.execute(str(qry))

def fetch_user(user_id: int):
  gs_user = Table('gs_user')
  
  qry = Query.from_(
    gs_user
  ).select(
    '*',
  ).where(
    gs_user.user_id == Parameter('%s')
  )

  user = gsprod.fetchone(str(qry), (user_id,))

  if user is None:
    return None

  username = user['username']
  first_name = user['first_name']
  last_name = user['last_name']
  stripe_customer_id = user['stripe_customer_id']
  address1 = user['address1']
  city = user['city']
  state = user['state']
  zip_code = user['zip_code']

  return GSUser(
    user_id,
    username,
    first_name,
    last_name,
    stripe_customer_id,
    address1,
    city,
    state,
    zip_code
  )

def jwt_required(optional=False, fresh=False, refresh=False, locations=None):
  def decorator(func):
    @wraps(func)
    def jwtrequired(*args, **kwargs):
      auth_header = request.headers.get('Authorization')
      if auth_header != None and auth_header.split()[0] == 'Basic':
        if auth_header != 'Basic ' + app.config['ACCESS_TOKEN']:
          raise AuthError({ "code": "invalid_tenant",
                    "description":"You do not have access to this tenant." }, 403)
        return func(*args, **kwargs)
      verify_jwt_in_request(optional=optional, fresh=fresh, refresh=refresh, locations=locations)
      user = get_current_user()
      if config.getboolean('logging', 'log_requests'):
        logger.info(f"[user:{user.username if user is not None else 'Anonymous'}] [client:{request.remote_addr}] [request:{request}]")
      if user is not None:
        return func(*args, **kwargs)
      elif optional:
        return func(*args, **kwargs)

      return gs_make_response(status=GStatusCode.ERROR,
                              httpstatus=401)
    return jwtrequired
  return decorator

def requires_token(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth_header = request.headers.get('Authorization')
    if auth_header != 'Bearer ' + app.config['ACCESS_TOKEN']:
      raise AuthError({ "code": "invalid_tenant",
                  "description":"You do not have access to this tenant." }, 403)
    return f(*args, **kwargs)
  return decorated

def requires_all_permissions(*expected_args):
  def decorator(func):
    @wraps(func)
    def permissionsrequired(*args, **kwargs):
      user_id = get_jwt_identity()
      if user_id != None:
        permissions = []  
        row = gsprod.fetchall("SELECT f.permission_id, name FROM gs_user_permission f LEFT JOIN gs_permission i USING (permission_id) WHERE f.user_id = %s AND f.tenant_id = %s ORDER BY name ASC", (user_id, app.config['TENANT_ID'],))
        if row != None:
          for permission in row:
            permissions.append(permission['name'])
        if config.getboolean('logging', 'log_requests'):
          logger.info(f"[user:{user if user is not None else 'Anonymous'}] [client:{request.remote_addr}] [request:{request}]")
        is_owner = gsprod.fetchone("SELECT is_owner FROM gs_user_tenant WHERE tenant_id = %s AND user_id = %s and is_owner = 't'", (app.config['TENANT_ID'], user_id,))
        if is_owner != None:
          return func(*args, **kwargs)

        total_permissions = 0
        has_permissions = 0
        for expected_arg in expected_args:
          total_permissions = total_permissions + 1
          if expected_arg in permissions:
            has_permissions = has_permissions + 1
        if total_permissions == has_permissions:
          return func(*args, **kwargs)

      body = request.get_data().decode('utf-8')
      logger.error(f'[http:403] [user:{user_id}] [client:{request.remote_addr}] [request:{request.url}] [body:{body}]')
      return gs_make_response(message='Forbidden',
                              status=GStatusCode.ERROR,
                              httpstatus=403)
    return permissionsrequired
  return decorator

def requires_permission(*expected_args):
  def decorator(func):
    @wraps(func)
    def permissionsrequired(*args, **kwargs):
      auth_header = request.headers.get('Authorization')
      if auth_header != None and auth_header.split()[0] == 'Basic':
        if auth_header != 'Basic ' + app.config['ACCESS_TOKEN']:
          return gs_make_response(message='Forbidden',
                          status=GStatusCode.ERROR,
                          httpstatus=403)
        permissions = ['ViewFranchises', 'ViewLocations', 'ViewMenus', 'ViewItems']
        for expected_arg in expected_args:
          if expected_arg in permissions:
            return func(*args, **kwargs)

      user_id = get_jwt_identity()
      if user_id != None:
        permissions = []  
        row = gsprod.fetchall("SELECT f.permission_id, name FROM gs_user_permission f LEFT JOIN gs_permission i USING (permission_id) WHERE f.user_id = %s AND f.tenant_id = %s ORDER BY name ASC", (user_id, app.config['TENANT_ID'],))
        if row != None:
          for permission in row:
            permissions.append(permission['name'])
        if config.getboolean('logging', 'log_requests'):
          logger.info(f"[user:{user if user is not None else 'Anonymous'}] [client:{request.remote_addr}] [request:{request}]")
        is_owner = gsprod.fetchone("SELECT is_owner FROM gs_user_tenant WHERE tenant_id = %s AND user_id = %s and is_owner = 't'", (app.config['TENANT_ID'], user_id,))
        if is_owner != None:
          return func(*args, **kwargs)
        for expected_arg in expected_args:
          if expected_arg in permissions:
            return func(*args, **kwargs)
      body = request.get_data().decode('utf-8')
      logger.error(f'[http:403] [user:{user_id}] [client:{request.remote_addr}] [request:{request.url}] [body:{body}]')
      return gs_make_response(message='Forbidden',
                              status=GStatusCode.ERROR,
                              httpstatus=403)
    return permissionsrequired
  return decorator

@jwt.additional_claims_loader
def add_claims_to_access_token(user: GSUser) -> dict:
  return {
    'id': user.id
  }

@jwt.user_identity_loader
def user_identity_lookup(user: GSUser) -> str:
  return user.id

@jwt.user_lookup_loader
def user_loader(header: dict, identity: dict) -> GSUser:
  return fetch_user(identity['sub'])

@jwt.invalid_token_loader
def invalid_token_loader(identity: dict) -> Response:
  return gs_make_response(status=GStatusCode.ERROR,
                          httpstatus=401)

@jwt.token_verification_failed_loader
def token_verification_failed_loader(header: dict, identity: dict) -> Response:
  return gs_make_response(status=GStatusCode.ERROR,
                          httpstatus=401)

@jwt.token_in_blocklist_loader
def is_token_revoked(decoded_header: dict, decoded_token: dict) -> bool:
  try:
    jti = decoded_token['jti']
    token = gsprod.fetchone(""" SELECT jwt_revoked
                                FROM gs_jwt
                               WHERE jwt_jti = %s;""", (jti,))
    if token is not None:
      return token['jwt_revoked']
    return True
  except Exception as e:
    logger.exception(e)
    return True

@jwt.user_lookup_error_loader
def custom_user_loader_error(header: str, identity: str) -> Response:
  return gs_make_response(status=GStatusCode.ERROR,
                          httpstatus=401)

@jwt.expired_token_loader
def expired_token_callback(header: dict, expired_token: dict) -> Response:
  token_type = expired_token['type']
  return gs_make_response(message=f'The {token_type} token has expired',
                          status=GStatusCode.ERROR,
                          httpstatus=401)

@jwt.unauthorized_loader
def unauth_handler(reason: str) -> Response:
  try:
    body = request.get_data().decode('utf-8')
    msg = f'[http:401] [client:{request.remote_addr}] [request:{request.url}] [body:{body}] [reason: {reason}]'
    logger.error(msg)
  except Exception as e:
    logger.exception(e)
  return gs_make_response(status=GStatusCode.ERROR,
                          httpstatus=401)

@authentication.route('/auth/whoami', methods=['GET'])
@jwt_required()
def whoami() -> Response:
  try:
    user = fetch_user(get_jwt_identity())
    jwt = get_jwt()
    access_token = request.cookies.get('_grubstack_access_token')
    refresh_token = request.cookies.get('_grubstack_refresh_token')
    decoded_access_token = decode_token(access_token)
    decoded_refresh_token = decode_token(refresh_token)
    user = {
      'username': user.username,
      'first_name': user.first_name,
      'last_name': user.last_name,
      'stripe_customer_id': user.stripe_customer_id,
      'access_token': access_token,
      'access_token_expiration': decoded_access_token['exp'],
      'access_token_expires_in': decoded_access_token['exp'] - time.time(),
      'access_token_jti': decoded_access_token['jti'],
      'refresh_token': refresh_token,
      'refresh_token_expiration': decoded_refresh_token['exp'],
      'refresh_token_expires_in': decoded_refresh_token['exp'] - time.time(),
      'refresh_token_jti': decoded_refresh_token['jti']
    }

    permissions = []

    is_owner = gsprod.fetchone("SELECT is_owner FROM gs_user_tenant WHERE tenant_id = %s AND user_id = %s", (app.config['TENANT_ID'], get_jwt_identity(),))
    if is_owner[0] == True:
      row = gsprod.fetchall("SELECT name FROM gs_permission")
      if row != None:
        for permission in row:
          permissions.append(permission['name'])

    else:
      row = gsprod.fetchall("SELECT f.permission_id, name FROM gs_user_permission f LEFT JOIN gs_permission i USING (permission_id) WHERE f.user_id = %s and f.tenant_id = %s ORDER BY name ASC", (get_jwt_identity(), app.config['TENANT_ID'],))
      if row != None:
        for permission in row:
          permissions.append(permission['name'])

    user['permissions'] = permissions
    user['tenant_id'] = app.config['TENANT_ID']

    return gs_make_response(data=user)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(data={},
                            httpstatus=500,
                            status=GStatusCode.ERROR)

@authentication.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh() -> Response:
  try:
    current_user = get_jwt_identity()
    jwt = get_jwt()
    user = fetch_user(current_user)
    access_token = create_access_token(identity=user)
    refresh_token = request.cookies.get('_grubstack_refresh_token') or request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_access_token = decode_token(access_token)
    decoded_refresh_token = decode_token(refresh_token)
    add_token_to_database(access_token, app.config['JWT_IDENTITY_CLAIM'], user.username)
    token = {
      'username': user.username,
      'first_name': user.first_name,
      'last_name': user.last_name,
      'stripe_customer_id': user.stripe_customer_id,
      'access_token': access_token,
      'access_token_expiration': decoded_access_token['exp'],
      'access_token_expires_in': decoded_access_token['exp'] - time.time(),
      'access_token_jti': decoded_access_token['jti'],
      'refresh_token': refresh_token,
      'refresh_token_expiration': decoded_refresh_token['exp'],
      'refresh_token_expires_in': decoded_refresh_token['exp'] - time.time(),
      'refresh_token_jti': decoded_refresh_token['jti']
    }

    response = make_response(jsonify({ "data": token }))
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response, 201

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to refresh token',
                            status=GStatusCode.ERROR,
                            httpstatus=500)
@authentication.route('/auth/verify_tenant', methods=['GET'])
@jwt_required()
def verify_tenant():
  row = gsprod.fetchall("SELECT * FROM gs_user_tenant WHERE user_id = %s AND tenant_id = %s", (get_jwt_identity(), app.config['TENANT_ID'],))
  if len(row) <= 0:
    raise AuthError({"code": "invalid_tenant",
                    "description": "You do not have access to this tenant app."}, 403)
  return gs_make_response(message='Success.')

@authentication.route('/auth/logout', methods=['POST'])
def logout():
    resp = jsonify({})
    unset_jwt_cookies(resp)
    return resp, 201

app.register_blueprint(authentication, url_prefix=config.get('general', 'urlprefix', fallback='/'))
