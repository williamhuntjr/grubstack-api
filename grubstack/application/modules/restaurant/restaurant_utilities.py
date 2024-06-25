def format_property(tenant_property: dict = {}):
  json_data = {
    "key": tenant_property['key'],
    "value": tenant_property['value'],
  }

  return json_data