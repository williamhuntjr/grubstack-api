import logging, json

from flask import Blueprint, url_for, request

from grubstack import app, config
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission

from grubstack.application.utilities.request import verify_params
from grubstack.application.utilities.filters import generate_filters, create_pagination_params

from .employees_utilities import format_params
from .employees_constants import REQUIRED_FIELDS, EMPLOYEE_FILTERS

from .employees_service import EmployeeService

employee = Blueprint('employee', __name__)
logger = logging.getLogger('grubstack')

employee_service = EmployeeService()

@employee.route('/employees', methods=['GET'])
@jwt_required()
@requires_permission("ViewEmployees", "MaintainEmployees")
def get_all():
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = employee_service.get_all(page, limit, generate_filters(EMPLOYEE_FILTERS, request.args))

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
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      verify_params(params, REQUIRED_FIELDS)

      employee = employee_service.search(params['first_name'], params['last_name'])

      if employee is not None:
        return gs_make_response(message='An employee with the provided first and last name already exists. Try a different name combination',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
      else:
        employee_service.create(format_params(params))
        employee = employee_service.search(params['first_name'], params['last_name'])

        headers = {'Location': url_for('employee.get', employee_id=employee['id'])}
        return gs_make_response(message='Employee created successfully',
                              httpstatus=201,
                              headers=headers,
                              data=employee)
    else:
      return gs_make_response(message='Invalid request',
                              status=GStatusCode.ERROR,
                              httpstatus=400)

  except ValueError as e:
    return gs_make_response(message=e,
                            status=GStatusCode.ERROR,
                            httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create employee',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@employee.route('/employees/<int:employee_id>', methods=['GET'])
@jwt_required()
@requires_permission("ViewEmployees", "MaintainEmployees")
def get(employee_id: int):
  try:
    employee = employee_service.get(employee_id, generate_filters(LOCATION_FILTERS, request.args))
    
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

@employee.route('/employees/<int:employee_id>', methods=['PATCH'])
@jwt_required()
@requires_permission("MaintainEmployees")
def update(employee_id: int):
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']

      if employee_id:
        employee = employee_service.get(employee_id)

        if employee is None:
          return gs_make_response(message='Employee not found',
                                  status=GStatusCode.ERROR,
                                  httpstatus=404)
        else:
          employee_service.update(employee_id, format_params(params, employee))
          employee = employee_service.get(employee_id)

          headers = {'Location': url_for('employee.get', employee_id=employee_id)}
          return gs_make_response(message=f'Employee #{employee_id} updated',
                    httpstatus=201,
                    headers=headers,
                    data=employee)

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
