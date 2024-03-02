import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission
from grubstack.application.utilities.filters import create_pagination_params

from .employees_service import EmployeeService
from .employees_utilities import format_params

employee = Blueprint('employee', __name__)
logger = logging.getLogger('grubstack')

employee_service = EmployeeService()

@employee.route('/employees', methods=['GET'])
@jwt_required()
@requires_permission("ViewEmployees")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = employee_service.get_all(page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve employees. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@employee.route('/employees', methods=['POST'])
@jwt_required()
@requires_permission("MaintainEmployees")
def create():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title = format_params(params)

      if first_name and last_name and gender and address1 and city and state and postal:
        employee = employee_service.search(first_name, last_name)
        
        if employee is not None:
          return gs_make_response(message='That employee already exists. Try a different first name and last name.',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          employee_service.create(format_params(params))
          employee = employee_service.search(first_name, last_name)

          if employee is not None:
            headers = {'Location': url_for('employee.get', employee_id=employee['id'])}
            return gs_make_response(message=f'Employee {first_name} {last_name} successfully created',
                                httpstatus=201,
                                headers=headers,
                                data=employee)
          else:
            return gs_make_response(message='Unable to create employee',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create employee',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@employee.route('/employees/<int:employee_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewEmployees")
def get(employee_id: int):
  try:
    employee = employee_service.get(employee_id)
    
    if employee:
      return gs_make_response(data=employee)

    else:
      return gs_make_response(message='Employee not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@employee.route('/employees/<int:employee_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainEmployees")
def delete(employee_id: int):
  try:
    employee = employee_service.get(employee_id)
    
    if employee is None:
      return gs_make_response(message='Employee not found',
                              status=GStatusCode.ERROR,
                              httpstatus=404)
    else:
      employee_service.delete(employee_id)
      return gs_make_response(message=f'Employee #{employee_id} deleted')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@employee.route('/employees', methods=['PUT'])
@jwt_required()
@requires_permission("MaintainEmployees")
def update():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      employee_id = params['id']
      first_name, last_name, gender, address1, city, state, postal, phone, email, profile_thumbnail_url, hire_date, employment_status, job_title = format_params(params)

      if employee_id and first_name and last_name and gender and address1 and city and state and postal:
        employee = employee_service.get(employee_id)

        if employee is None:
          return gs_make_response(message=f'Employee {first_name} {last_name} does not exist',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          employee_service.update(employee_id, format_params(params))
          headers = {'Location': url_for('employee.get', employee_id=employee_id)}
          return gs_make_response(message=f'Employee {first_name} {last_name} successfully updated',
                    httpstatus=201,
                    headers=headers)

      else:
        return gs_make_response(message='Invalid request',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update employee',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(employee, url_prefix=config.get('general', 'urlprefix', fallback='/'))
