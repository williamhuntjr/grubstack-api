import json, requests
from six.moves.urllib.request import urlopen

from functools import wraps
from jose import jwt

from flask import request, _request_ctx_stack, Blueprint

from . import app, config, logger, gsprod, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode

AUTH0_DOMAIN = app.config['AUTH0_DOMAIN']
AUTH0_AUDIENCE = app.config['AUTH0_AUDIENCE']

ALGORITHMS = ["RS256"]

gsauth = Blueprint('auth', __name__)

class AuthError(Exception):
  def __init__(self, error, status_code):
    self.error = error
    self.status_code = status_code

def get_token_auth_header():
  auth = request.headers.get("Authorization", None)
  if not auth:
    raise AuthError({ "code": "authorization_header_missing",
                      "description": "Authorization header is expected" }, 401)

  parts = auth.split()

  if parts[0].lower() != "bearer":
    raise AuthError({ "code": "invalid_header",
                      "description": "Authorization header must start with Bearer" }, 401)
  elif len(parts) == 1:
    raise AuthError({ "code": "invalid_header",
                      "description": "Token not found" }, 401)
  elif len(parts) > 2:
    raise AuthError({ "code": "invalid_header",
                      "description": "Authorization header must be Bearer token" }, 401)

  token = parts[1]
  return token

def get_user_info():
  current_user = _request_ctx_stack.top.current_user
  return current_user

def get_user_id():
  current_user = _request_ctx_stack.top.current_user
  return current_user['sub'] if 'sub' in current_user else None
  
def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth_header = request.headers.get('Authorization')
    if auth_header != None and auth_header.split()[0] == 'Basic':
      if auth_header != 'Basic ' + app.config['ACCESS_TOKEN']:
        raise AuthError({ "code": "invalid_tenant",
                  "description":"You do not have access to this tenant." }, 403)
      return f(*args, **kwargs)
    token = get_token_auth_header()
    if token.split()[0] != 'Basic':
      jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
      jwks = json.loads(jsonurl.read())
      unverified_header = jwt.get_unverified_header(token)
      rsa_key = {}
      for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
          rsa_key = {
            "kty": key["kty"],
            "kid": key["kid"],
            "use": key["use"],
            "n": key["n"],
            "e": key["e"]
          }
      if rsa_key:
        try:
          payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer="https://"+AUTH0_DOMAIN+"/"
          )
        except jwt.ExpiredSignatureError:
            raise AuthError({ "code": "token_expired",
                              "description": "token is expired" }, 401)
        except jwt.JWTClaimsError:
            raise AuthError({ "code": "invalid_claims",
                              "description":"incorrect claims, please check the audience and issuer" }, 401)
        except Exception:
            raise AuthError({ "code": "invalid_header",
                              "description":"Unable to parse authentication token." }, 401)

        _request_ctx_stack.top.current_user = payload
        row = gsprod.fetchall("SELECT * FROM gs_user_tenant WHERE user_id = %s AND tenant_id = %s", (payload['sub'], app.config['TENANT_ID'],))

        if len(row) <= 0:
            raise AuthError({ "code": "invalid_tenant",
                              "description":"You do not have access to this tenant." }, 403)
        return f(*args, **kwargs)
      raise AuthError({ "code": "invalid_header",
                        "description": "Unable to find appropriate key" }, 401)
  return decorated

def requires_token(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth_header = request.headers.get('Authorization')
    if auth_header != 'Bearer ' + app.config['ACCESS_TOKEN']:
      raise AuthError({ "code": "invalid_tenant",
                  "description":"You do not have access to this tenant." }, 403)
    return f(*args, **kwargs)
  return decorated

def requires_scope(required_scope):
  def decorator(func):
    @wraps(func)
    def scope_required(*args, **kwargs):
      token = get_token_auth_header()
      unverified_claims = jwt.get_unverified_claims(token)
      user_id = get_user_id()
      if config.getboolean('logging', 'log_requests'):
        logger.info(f"[user:{'Anonymous'}] [client:{request.remote_addr}] [request:{request}]")
      if unverified_claims.get("scope"):
        token_scopes = unverified_claims["scope"].split()
        for token_scope in token_scopes:
          if token_scope == required_scope:
            return func(*args, **kwargs)
        body = request.get_data().decode('utf-8')
        logger.error(f'[http:403] [user:{user_id}] [client:{request.remote_addr}] [request:{request.url}] [body:{body}]')
      raise AuthError({ "code": "Unauthorized",
                        "description": "You don't have access to this resource" }, 403)
    return scope_required
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
        permissions = ['ViewFranchises', 'ViewStores', 'ViewMenus', 'ViewItems']
        for expected_arg in expected_args:
          if expected_arg in permissions:
            return func(*args, **kwargs)

      user_id = get_user_id()
      if user_id != None:
        permissions = []  
        row = gsdb.fetchall("SELECT f.permission_id, name FROM gs_user_permission f LEFT JOIN gs_permission i USING (permission_id) WHERE f.user_id = %s ORDER BY name ASC", (user_id,))
        if row != None:
          for permission in row:
            permissions.append(permission['name'])
        if config.getboolean('logging', 'log_requests'):
          logger.info(f"[user:{user if user is not None else 'Anonymous'}] [client:{request.remote_addr}] [request:{request}]")
        is_owner = gsprod.fetchone("SELECT is_owner FROM gs_user_tenant WHERE tenant_id = %s AND user_id = %s", (app.config['TENANT_ID'], user_id,))
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

def requires_role(*expected_args):
  def decorator(func):
    @wraps(func)
    def rolesrequired(*args, **kwargs):
      user_id = get_user_id()
      if user_id != None:
        roles = []  
        row = gsdb.fetchall("SELECT f.role_id, name FROM gs_user_role f LEFT JOIN gs_role i USING (role_id) WHERE f.user_id = %s ORDER BY name ASC", (user_id,))
        if row != None:
          for role in row:
            roles.append(role['name'])
        if config.getboolean('logging', 'log_requests'):
          logger.info(f"[user:{user if user is not None else 'Anonymous'}] [client:{request.remote_addr}] [request:{request}]")
        for expected_arg in expected_args:
          if expected_arg in roles:
            return func(*args, **kwargs)
      body = request.get_data().decode('utf-8')
      logger.error(f'[http:403] [user:{user_id}] [client:{request.remote_addr}] [request:{request.url}] [body:{body}]')
      return gs_make_response(message='Forbidden',
                              status=GStatusCode.ERROR,
                              httpstatus=403)
    return rolesrequired
  return decorator

@gsauth.route('/auth/userinfo', methods=['GET'])
@requires_auth
def get_userinfo():
  token = get_token_auth_header()
  jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
  jwks = json.loads(jsonurl.read())
  unverified_header = jwt.get_unverified_header(token)
  rsa_key = {}
  for key in jwks["keys"]:
    if key["kid"] == unverified_header["kid"]:
      rsa_key = {
        "kty": key["kty"],
        "kid": key["kid"],
        "use": key["use"],
        "n": key["n"],
        "e": key["e"]
      }
  if rsa_key:
    try:
      payload = jwt.decode(
        token,
        rsa_key,
        algorithms=ALGORITHMS,
        audience=AUTH0_AUDIENCE,
        issuer="https://"+AUTH0_DOMAIN+"/"
      )
    except jwt.ExpiredSignatureError:
      raise AuthError({ "code": "token_expired",
                        "description": "token is expired" }, 401)
    except jwt.JWTClaimsError:
      raise AuthError({ "code": "invalid_claims",
                        "description":"incorrect claims, please check the audience and issuer" }, 401)
    except Exception:
      raise AuthError({ "code": "invalid_header",
                        "description":"Unable to parse authentication token." }, 401)

    resp = requests.get("https://"+AUTH0_DOMAIN+"/userinfo", headers={'Authorization': 'Bearer '+token})
    json_data = resp.json()
    
    permissions = []

    is_owner = gsprod.fetchone("SELECT is_owner FROM gs_user_tenant WHERE tenant_id = %s AND user_id = %s", (app.config['TENANT_ID'], json_data['sub'],))
    if is_owner:
      row = gsdb.fetchall("SELECT name FROM gs_permission")
      if row != None:
        for permission in row:
          permissions.append(permission['name'])

    else:
      row = gsdb.fetchall("SELECT f.permission_id, name FROM gs_user_permission f LEFT JOIN gs_permission i USING (permission_id) WHERE f.user_id = %s ORDER BY name ASC", (json_data['sub'],))
      if row != None:
        for permission in row:
          permissions.append(permission['name'])

    json_data['permissions'] = permissions
    json_data['tenant_id'] = app.config['TENANT_ID']
    return gs_make_response(data=json_data)
  raise AuthError({ "code": "invalid_header",
                    "description": "Unable to find appropriate key" }, 401)

@gsauth.route('/auth/verify_tenant', methods=['GET'])
@requires_auth
def verify_tenant():
  token = get_token_auth_header()
  jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
  jwks = json.loads(jsonurl.read())
  unverified_header = jwt.get_unverified_header(token)
  rsa_key = {}
  for key in jwks["keys"]:
    if key["kid"] == unverified_header["kid"]:
      rsa_key = {
        "kty": key["kty"],
        "kid": key["kid"],
        "use": key["use"],
        "n": key["n"],
        "e": key["e"]
      }
  if rsa_key:
    try:
      payload = jwt.decode(
        token,
        rsa_key,
        algorithms=ALGORITHMS,
        audience=AUTH0_AUDIENCE,
        issuer="https://"+AUTH0_DOMAIN+"/"
      )
    except jwt.ExpiredSignatureError:
      raise AuthError({ "code": "token_expired",
                        "description": "token is expired" }, 401)
    except jwt.JWTClaimsError:
      raise AuthError({ "code": "invalid_claims",
                        "description":"incorrect claims, please check the audience and issuer" }, 401)
    except Exception:
      raise AuthError({ "code": "invalid_header",
                        "description":"Unable to parse authentication token." }, 401)

    row = gsprod.fetchall("SELECT * FROM gs_user_tenant WHERE user_id = %s AND tenant_id = %s", (payload['sub'], app.config['TENANT_ID'],))
    if len(row) <= 0:
      raise AuthError({"code": "invalid_tenant",
                      "description": "You do not have access to this tenant app."}, 403)
    return gs_make_response(message='Success.')
  raise AuthError({ "code": "invalid_header",
                    "description": "Unable to find appropriate key" }, 401)

app.register_blueprint(gsauth, url_prefix=config.get('general', 'urlprefix', fallback='/'))
