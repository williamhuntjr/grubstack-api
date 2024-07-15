from grubstack import app, gsdb

from pypika import Query, Table, Order, Parameter

from .restaurant_utilities import format_order_type, format_working_hour_type

class RestaurantService:
  def __init__(self):
    pass

  def get_working_hour_types(self):
    gs_working_hour_type = Table('gs_working_hour_type')

    qry = Query.from_(
      gs_working_hour_type
    ).select(
      '*'
    )

    working_hour_types = gsdb.fetchall(str(qry))

    working_hour_types_list = []
    for working_hour_type in working_hour_types:
      working_hour_types_list.append(format_working_hour_type(working_hour_type))

    return working_hour_types_list
  
  def get_order_types(self):
    gs_order_types = Table('gs_order_type')

    qry = Query.from_(
      gs_order_types
    ).select(
      '*'
    )

    order_types = gsdb.fetchall(str(qry))

    order_types_list = []
    for order_type in order_types:
      order_types_list.append(format_order_type(order_type))

    return order_types_list
  
  def get_order_type(self, order_type_id: int):
    gs_order_type = Table('gs_order_type')

    qry = Query.from_(
      gs_order_type
    ).select(
      '*'
    ).where(
      gs_order_type.order_type_id == Parameter('%s')
    )

    order_type = gsdb.fetchone(str(qry), (order_type_id,))

    return format_order_type(order_type)

  def get_working_hour_type(self, working_hour_type_id: int):
    gs_working_hour_type = Table('gs_working_hour_type')

    qry = Query.from_(
      gs_working_hour_type
    ).select(
      '*'
    ).where(
      gs_working_hour_type.working_hour_type_id == Parameter('%s')
    )

    working_hour_type = gsdb.fetchone(str(qry), (working_hour_type_id,))

    return format_working_hour_type(working_hour_type)