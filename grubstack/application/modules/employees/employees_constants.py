from grubstack import app

PER_PAGE = app.config['PER_PAGE']

REQUIRED_FIELDS = [
  'first_name',
  'last_name',
  'gender',
  'address1',
  'city',
  'state',
  'postal'
]
EMPLOYEE_FILTERS = {}
DEFAULT_FILTERS = []