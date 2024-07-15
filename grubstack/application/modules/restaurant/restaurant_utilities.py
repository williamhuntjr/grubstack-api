def format_order_type(order_type: dict = {}):
  json_data = {
    "id": order_type['order_type_id'],
    "name": order_type['name'],
    "description": order_type['description']
  }

  return json_data

def format_working_hour_type(working_hour_type: dict = {}):
  json_data = {
    "id": working_hour_type['working_hour_type_id'],
    "name": working_hour_type['name'],
  }

  return json_data