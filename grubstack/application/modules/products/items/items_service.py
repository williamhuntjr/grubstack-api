from pypika import Query, Table, Order, Parameter

from grubstack import app, gsdb
from grubstack.application.utilities.filters import generate_paginated_data

from .items_utilities import format_item
from .items_constants import PER_PAGE

class ItemService:
  def __init__(self):
    pass

  def apply_filters(self, item: dict, filters: list = []):
    return format_item(item, filters)

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    gs_item = Table('gs_item')

    qry = Query.from_(
      gs_item
    ).select(
      '*'
    ).orderby(
      gs_item.name, order=Order.asc
    ) 

    items = gsdb.fetchall(str(qry))

    filtered = []

    for item in items:
      filtered.append(self.apply_filters(item, filters))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, item_id: int, filters: list = []):
    gs_item = Table('gs_item')
    qry = Query.from_(
      gs_item
    ).select(
      '*'
    ).where(
      gs_item.item_id == item_id
    )

    item = gsdb.fetchone(str(qry))

    if item is not None:
      filtered_data = self.apply_filters(item, filters)
      return filtered_data

    else:
      return None

  def search(self, name: str, filters: list = []):
    gs_item = Table('gs_item')
    qry = Query.from_(
      gs_item
    ).select(
      '*'
    ).where(
      gs_item.name == name
    )

    item = gsdb.fetchone(str(qry))

    if item is not None:
      filtered_data = self.apply_filters(item, filters)
      return filtered_data

    else:
      return None

  def delete(self, item_id: int):
    gs_item = Table('gs_item')
    qry = Query.from_(
      gs_item
    ).delete().where(
      gs_item.item_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (item_id,))

    gs_menu_item = Table('gs_menu_item')
    qry = Query.from_(
      gs_menu_item
    ).delete().where(
      gs_menu_item.item_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (item_id,))

  def create(self, params: dict = ()):
    name, description, thumbnail_url = params

    gs_item = Table('gs_item')
    qry = Query.into(
      gs_item
    ).columns(
      gs_item.tenant_id,
      gs_item.name,
      gs_item.description,
      gs_item.thumbnail_url
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s')
    )

    return gsdb.execute(str(qry), (name, description, thumbnail_url,))

  def update(self, item_id: int, params: dict = ()):
    name, description, thumbnail_url = params

    gs_item = Table('gs_item')
    qry = Query.update(
      gs_item
    ).set(
      gs_item.name, Parameter('%s')
    ).set(
      gs_item.description, Parameter('%s')
    ).set(
      gs_item.thumbnail_url, Parameter('%s')
    ).where(
      gs_item.item_id == Parameter('%s')
    )

    return gsdb.execute(str(qry), (name, description, thumbnail_url, item_id,))
