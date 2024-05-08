from grubstack import app
from grubstack.application.utilities.reducers import field_reducer

def format_location(location: dict, menus_list: list = [], filters: list = []):
  json_data = {
    "id": location['location_id'],
    "name": location['name'],
    "address1": location['address1'],
    "city": location['city'],
    "state": location['state'],
    "postal": location['postal'],
    "location_type": location['location_type'],
    "phone_number": location['phone_number'],
    "create_date": location['create_date'],
    "is_active": location['is_active']
  }

  if 'showMenus' in filters and filters['showMenus']:
    json_data['menus'] = menus_list

  return json_data

def format_params(params: dict, location: dict = {}):
  name = field_reducer('name', params, location, '')
  address1 = field_reducer('address1', params, location, '')
  city = field_reducer('city', params, location, '')
  state = field_reducer('state', params, location, '')
  postal = field_reducer('postal', params, location, '')
  location_type = field_reducer('location_type', params, location, 'restaurant')
  phone_number = field_reducer('phone_number', params, location, '')
  is_active = field_reducer('is_active', params, location, '')

  return (name, address1, city, state, postal, location_type, phone_number, is_active)