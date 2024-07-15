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

def format_work_hour(work_hour: dict):
  json_data = {
    "working_hour_type_id": work_hour['working_hour_type_id'],
    "day": work_hour['day'],
    "open_hour": work_hour['open_hour'],
    "open_minute": work_hour['open_minute'],
    "close_hour": work_hour['close_hour'],
    "close_minute": work_hour['close_minute'],
    "is_open": work_hour['is_open'],
  }

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

def format_work_hour_params(params: dict):
  day = params['day']
  open_hour = params['open_hour']
  open_minute = params['open_minute']
  close_hour = params['close_hour']
  close_minute = params['close_minute']
  is_open = params['is_open']

  return (day, open_hour, open_minute, close_hour, close_minute, is_open)

def format_property(location_property: dict = {}):
  json_data = {
    "location_id": location_property['location_id'],
    "key": location_property['key'],
    "value": location_property['value'],
  }

  return json_data
