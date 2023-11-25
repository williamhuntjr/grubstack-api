from grubstack import app

def format_franchise(franchise: dict, stores_list: list = [], filters: list = []):
  json_data = {
    "id": franchise['franchise_id'],
    "name": franchise['name'],
    "description": franchise['description'],
    "thumbnail_url": franchise['thumbnail_url']
  }
  if 'showStores' in filters and filters['showStores']:
    json_data['stores'] = stores_list

  return json_data
  
def format_params(params: dict):
  name = params['name']
  description = params['description'] or ''
  thumbnail_url = params['thumbnail_url'] or app.config['THUMBNAIL_PLACEHOLDER_IMG']

  return (name, description, thumbnail_url)