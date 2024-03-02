from pypika import Query, Table, Order, Parameter

from grubstack import app, gsdb
from grubstack.application.utilities.filters import generate_paginated_data

from .employees_constants import PER_PAGE
from .employees_utilities import format_employee

class EmployeeService:
  def __init__(self):
    pass

  def get_all(self, page: int = 1, limit: int = PER_PAGE, filters: list = []):
    gs_employee = Table('gs_employee')
    qry = Query.from_(
      gs_employee
    ).select(
      '*'
    ).orderby(
      gs_employee.hire_date, order=Order.asc
    )

    employees = gsdb.fetchall(str(qry))

    formatted = []
    for employee in employees:
      formatted.append(format_employee(employee))

    json_data, total_rows, total_pages = generate_paginated_data(formatted, page, limit)

    return (json_data, total_rows, total_pages)

  def get(self, employee_id: int):
    gs_employee = Table('gs_employee')
    qry = Query.from_(
      gs_employee
    ).select(
      '*'
    ).where(
      gs_employee.employee_id == employee_id
    )

    employee = gsdb.fetchone(str(qry))

    return format_employee(employee)

  def create(self, params: tuple = ()):
    first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title = params

    gs_employee = Table('gs_employee')
    qry = Query.into(
      gs_employee
    ).columns(
      gs_employee.tenant_id,
      gs_employee.first_name,
      gs_employee.last_name,
      gs_employee.gender,
      gs_employee.address1,
      gs_employee.city,
      gs_employee.state,
      gs_employee.postal,
      gs_employee.phone,
      gs_employee.email,
      gs_employee.profile_thumbnail_url,
      gs_employee.hire_date,
      gs_employee.employment_status,
      gs_employee.job_title
    ).insert(
      app.config['TENANT_ID'],
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
      Parameter('%s'),
    )
    
    return gsdb.execute(str(qry), (first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title))

  def update(self, employee_id: int, params: tuple = ()):
    first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title = params

    gs_employee = Table('gs_employee')
    qry = Query.update(
      gs_employee
    ).set(
      gs_employee.first_name, Parameter('%s')
    ).set(
      gs_employee.last_name, Parameter('%s')
    ).set(
      gs_employee.gender, Parameter('%s')
    ).set(
      gs_employee.address1, Parameter('%s')
    ).set(
      gs_employee.city, Parameter('%s')
    ).set(
      gs_employee.state, Parameter('%s')
    ).set(
      gs_employee.postal, Parameter('%s')
    ).set(
      gs_employee.phone, Parameter('%s')
    ).set(
      gs_employee.email, Parameter('%s')
    ).set(
      gs_employee.profile_thumbnail_url, Parameter('%s')
    ).set(
      gs_employee.hire_date, Parameter('%s')
    ).set(
      gs_employee.employment_status, Parameter('%s')
    ).set(
      gs_employee.job_title, Parameter('%s')
    ).where(
      gs_employee.employee_id == Parameter('%s')
    )

    return gsdb.execute(str(qry), (first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title, employee_id))

  def delete(self, employee_id: int):
    gs_employee = Table('gs_employee')
    qry = Query.from_(
      gs_employee
    ).delete().where(
      gs_employee.employee_id == Parameter('%s')
    )

    gsdb.execute(str(qry), (employee_id,))

  def search(self, first_name: str, last_name: str):
    gs_employee = Table('gs_employee')
    qry = Query.from_(
      gs_employee
    ).select(
      '*'
    ).where(
      gs_employee.first_name == Parameter('%s')
    ).where(
      gs_employee.last_name == Parameter('%s')
    )

    employee = gsdb.fetchone(str(qry), (first_name, last_name))

    if employee is not None:
      return format_employee(employee)
    
    return None
