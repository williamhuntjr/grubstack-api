def verify_params(json: dict, params: dict):
  missing_params = []
  for param in params:
    if param not in json:
      missing_params.append(param)
  
  if len(missing_params) > 0:
    raise ValueError('Missing required fields: ' + ', '.join(missing_params))
