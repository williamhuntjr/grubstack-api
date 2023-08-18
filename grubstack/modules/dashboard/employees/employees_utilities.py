from grubstack import app, gsdb
from math import ceil

PER_PAGE = app.config['PER_PAGE']

def formatEmployee(employee: dict):
  return {
    "id": employee['employee_id'],
    "first_name": employee['first_name'],
    "last_name": employee['last_name'],
    "gender": employee['gender'],
    "address1": employee['address1'],
    "city": employee['city'],
    "state": employee['state'],
    "postal": employee['postal'],
    "phone": employee['phone'],
    "email": employee['email'],
    "profile_thumbnail_url": employee['profile_thumbnail_url'],
    "hire_date": employee['hire_date'],
    "employment_status": employee['employment_status'],
    "job_title": employee['job_title'],
  }

def formatParams(params: dict):
  first_name = params['first_name']
  last_name = params['last_name'] 
  gender = params['gender'] 
  address1 = params['address1'] 
  city = params['city'] 
  state = params['state'] 
  postal = params['postal'] 
  phone = params['phone'] or 'N/A'
  email = params['email'] or 'N/A'
  profile_thumbnail_url = params['profile_thumbnail_url']
  hire_date = params['hire_date'] or datetime.now()
  employment_status = params['employment_status'] or 'employed'
  job_title = params['job_title']

  return (first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title)

def getEmployees(page: int = 1, limit: int = PER_PAGE):
  json_data = []
  employees = gsdb.fetchall("SELECT * FROM gs_employee ORDER BY hire_date ASC")

  employees_list = []
  for employee in employees:
    employees_list.append(formatEmployee(employee))

  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(employees) / limit)
  total_rows = len(employees)

  # Get paged data
  json_data = employees_list[start:end]

  return (json_data, total_rows, total_pages)