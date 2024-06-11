def field_reducer(field_name: str, params: dict, original: dict, fallback):
  result = fallback

  if field_name in original:
    result = original[field_name]

  if field_name in params:
    result = params[field_name]
    if params[field_name] == '' and fallback != '':
      result = fallback

  return result