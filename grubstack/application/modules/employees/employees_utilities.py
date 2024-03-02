from math import ceil
from datetime import datetime

from grubstack import app, gsdb

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

def format_params(params: dict):
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
  employment_status = params['employment_status'] or 'suspended'
  job_title = params['job_title']

  return (first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title)