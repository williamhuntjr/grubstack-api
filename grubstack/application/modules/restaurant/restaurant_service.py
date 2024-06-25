from grubstack import app, gsdb

from pypika import Query, Table, Order, Parameter

from .restaurant_utilities import format_property

class RestaurantService:
  def __init__(self):
    pass

  def get_all_properties(self):
    gs_tenant_property = Table('gs_tenant_property')

    qry = Query.from_(
      gs_tenant_property
    ).select(
      '*'
    ).orderby(
      gs_tenant_property.key, order=Order.asc
    )

    properties = gsdb.fetchall(str(qry))

    properties_list = []
    for tenant_property in properties:
      properties_list.append(format_property(tenant_property))
  
    return properties_list

  def property_exists(self, key: str):
    gs_tenant_property = Table('gs_tenant_property')
    qry = Query.from_(
      gs_tenant_property
    ).select(
      '*'
    ).where(
      gs_tenant_property.key == Parameter('%s')
    )
    
    tenant_property = gsdb.fetchone(str(qry), (key,))

    if tenant_property is not None:
      return True
    
    return False

  def get_property(self, key: str):
    gs_tenant_property = Table('gs_tenant_property')
    qry = Query.from_(
      gs_tenant_property
    ).select(
      '*'
    ).where(
      gs_tenant_property.key == Parameter('%s')
    )
    
    tenant_property = gsdb.fetchone(str(qry), (key,))

    return format_property(tenant_property)

  def update_property(self, key: str, value: str):
    gs_tenant_property = Table('gs_tenant_property')

    if self.property_exists(key):
      qry = Query.update(
        gs_tenant_property
      ).set(
        gs_tenant_property.value, Parameter('%s')
      ).where(
        gs_tenant_property.key == Parameter('%s')
      )

      return gsdb.execute(str(qry), (value, key,))

    else:
      qry = Query.into(
        gs_tenant_property
      ).columns(
        gs_tenant_property.tenant_id,
        gs_tenant_property.key,
        gs_tenant_property.value,
      ).insert(
        app.config['TENANT_ID'],
        Parameter('%s'),
        Parameter('%s'),
      )

      return gsdb.execute(str(qry), (key, value,))