import logging, json
from math import ceil
from flask import Blueprint, url_for, request
from datetime import datetime
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission

employee = Blueprint('employee', __name__)
logger = logging.getLogger('grubstack')
per_page = app.config['PER_PAGE']

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

@employee.route('/employees', methods=['GET'])
@requires_auth
@requires_permission("ViewEmployees")
def get_all():
  try:
    json_data = []
    employees = gsdb.fetchall("SELECT * FROM gs_employee ORDER BY hire_date ASC")
    
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = per_page
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    employees_list = []
    for employee in employees:
      employees_list.append(formatEmployee(employee))

    # Calculate paged data
    offset = page - 1
    start = offset * limit
    end = start + limit
    total_pages = ceil(len(employees) / limit)

    # Get paged data
    json_data = employees_list[start:end]

    return gs_make_response(data=json_data, totalrowcount=len(employees), totalpages=total_pages)

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
