import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from datetime import datetime
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission
from .employees_utilities import formatEmployee, getEmployees, formatParams

employee = Blueprint('employee', __name__)
logger = logging.getLogger('grubstack')

PER_PAGE = app.config['PER_PAGE']

@employee.route('/employees', methods=['GET'])
@requires_auth
@requires_permission("ViewEmployees")
def get_all():
  try:
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)
    
    json_data, total_rows, total_pages = getEmployees(page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve employees. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@employee.route('/employee/create', methods=['POST'])
@requires_auth
@requires_permission("MaintainEmployees")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title = formatParams(params)

      if first_name and last_name and gender and address1 and city and state and postal:
        # Check if exists
        row = gsdb.fetchall("SELECT * from gs_employee WHERE first_name = %s AND last_name = %s", (first_name, last_name,))

        if row is not None and len(row) > 0:
          return gs_make_response(message='That employee already exists. Try a different first name and last name.',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("""INSERT INTO gs_employee 
                                (tenant_id, employee_id, first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title)
                                VALUES
                                (%s, DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (app.config["TENANT_ID"], first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title,))
          row = gsdb.fetchone("SELECT * FROM gs_employee WHERE first_name = %s AND last_name = %s", (first_name, last_name,))
          if row is not None and len(row) > 0:
            headers = {'Location': url_for('employee.get', employee_id=row['employee_id'])}
            return gs_make_response(message=f'Employee {first_name} {last_name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=row)
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create employee',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@employee.route('/employee/<string:employee_id>', methods=['GET'])
@requires_auth
@requires_permission("ViewEmployees")
def get(employee_id: int):
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)

      # Check if exists
      row = gsdb.fetchone("SELECT * FROM gs_employee WHERE employee_id = %s", (employee_id,))
      if row: 
        json_data = formatEmployee(row)

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@employee.route('/employee/delete', methods=['POST'])
@requires_auth
@requires_permission("MaintainEmployees")
def delete():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      employee_id = params['employee_id']

      if employee_id:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_employee WHERE employee_id = %s", (employee_id,))
        if row is None:
          return gs_make_response(message='Invalid employee',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          qry = gsdb.execute("DELETE FROM gs_employee WHERE employee_id = %s", (employee_id,))
          return gs_make_response(message=f'Employee #{employee_id} deleted')

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@employee.route('/employee/update', methods=['POST'])
@requires_auth
@requires_permission("MaintainEmployees")
def update():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      employee_id = params['id']
      first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title = formatParams(params)

      if employee_id and first_name and last_name and gender and address1 and city and state and postal:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_employee WHERE employee_id = %s", (employee_id,))

        if row is None:
          return gs_make_response(message=f'Employee {first_name} {last_name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          qry = gsdb.execute("""UPDATE gs_employee SET 
                                (first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title) = (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                                WHERE employee_id = %s""", (first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title, employee_id,))
          headers = {'Location': url_for('employee.get', employee_id=employee_id)}
          return gs_make_response(message=f'Employee {first_name} {last_name} successfully updated',
                    httpstatus=201,
                    headers=headers,
                    data=json_data)

      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update employee',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(employee, url_prefix=config.get('general', 'urlprefix', fallback='/'))
