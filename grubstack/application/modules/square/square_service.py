import requests

from square.client import Client
from square.http.auth.o_auth_2 import BearerAuthCredentials

from pypika import Query, Table, Tables, Order, functions, Parameter

from grubstack import app, gsprod

from .square_utilities import decrypt

class SquareService:
  def __init__(self, client = None):
    with app.app_context():
      access_token = self.get_access_token()
      if access_token:
        client = Client(
          bearer_auth_credentials=BearerAuthCredentials(
            access_token=access_token
          ),
          environment=app.config['SQUARE_ENVIRONMENT'])
        self.client = client
    
  def get_access_token(self):
    tenant_id = app.config['TENANT_ID']
  
    gs_tenant_square = Table('gs_tenant_square')

    qry = Query.from_(
      gs_tenant_square
    ).select(
      gs_tenant_square.access_token
    ).where(
      gs_tenant_square.tenant_id == tenant_id
    )

    access_token = gsprod.fetchone(str(qry))

    if access_token is not None:
      return decrypt(access_token[0])

    return None
  
  def get_locations(self):
    if self.client is not None:
      result = self.client.locations.list_locations()
      if result.is_success():
        return result.body['locations']

    return []