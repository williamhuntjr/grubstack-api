def format_property(tenant_property: dict = {}):
  json_data = {
    "key": tenant_property['key'],
    "value": tenant_property['value'],
  }

  return json_data

def format_order_type(order_type: dict = {}):
  json_data = {
    "id": order_type['order_type_id'],
    "name": order_type['name'],
    "description": order_type['description']
  }

  return json_data