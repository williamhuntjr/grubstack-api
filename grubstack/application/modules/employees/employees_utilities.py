from datetime import datetime

from grubstack import app
from grubstack.application.utilities.reducers import field_reducer

PER_PAGE = app.config['PER_PAGE']

def format_employee(employee: dict):
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

def format_params(params: dict, employee: dict = {}):  
  first_name = field_reducer('first_name', params, employee, '')
  last_name = field_reducer('last_name', params, employee, '')
  gender = field_reducer('gender', params, employee, '')
  address1 = field_reducer('address1', params, employee, '')
  city = field_reducer('city', params, employee, '')
  state = field_reducer('state', params, employee, '')
  postal = field_reducer('postal', params, employee, '')
  phone = field_reducer('phone', params, employee, 'N/A')
  email = field_reducer('email', params, employee, 'N/A')
  profile_thumbnail_url = field_reducer('profile_thumbnail_url', params, employee, app.config['THUMBNAIL_PERSON_PLACEHOLDER_IMG'])
  hire_date = field_reducer('hire_date', params, employee, datetime.now())
  employment_status = field_reducer('employment_status', params, employee, 'suspended')
  job_title = field_reducer('job_title', params, employee, '')

  return (first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title)