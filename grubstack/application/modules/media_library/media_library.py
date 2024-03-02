import logging, os, subprocess, json

from flask import Blueprint, request
from werkzeug.utils import secure_filename

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import jwt_required, requires_permission

from grubstack.application.utilities.filters import create_pagination_params

from .media_library_utilities import allowed_file
from .media_library_service import MediaLibraryService

media_library = Blueprint('media_library', __name__)
logger = logging.getLogger('grubstack')

media_library_service = MediaLibraryService()

@media_library.route('/media-library', methods=['GET'])
@jwt_required()
@requires_permission('ViewMediaLibrary')
def get_all():
  try:
    page, limit = create_pagination_params(request.args)

    json_data, total_rows, total_pages = media_library_service.get_all(page, limit)

    return gs_make_response(data=json_data, totalrowcount=total_rows, totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve files. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@media_library.route('/media-library', methods=['POST'])
@jwt_required()
@requires_permission('MaintainMediaLibrary')
def upload():
  try:
    if 'file' not in request.files:
      return gs_make_response(message='No files uploaded. Please try again',
                          status=GStatusCode.ERROR,
                          httpstatus=400)

    file = request.files['file']

    if file and file.filename == '':
      return gs_make_response(message='No files uploaded. Please try again',
                          status=GStatusCode.ERROR,
                          httpstatus=400)
    
    if file and allowed_file(file.filename):
      media_library_service.upload(file)
      return gs_make_response(message='File uploaded successfully',
                      status=GStatusCode.SUCCESS,
                      httpstatus=200)
  
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to upload file',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@media_library.route('/media-library/<int:file_id>', methods=['DELETE'])
@jwt_required()
@requires_permission("MaintainMediaLibrary")
def delete(file_id: int):
  try:
    if file_id:
      file_data = media_library_service.get(file_id)
      if file_data is None:
        return gs_make_response(message='Invalid file',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
      else:
        media_library_service.delete(file_id)
        return gs_make_response(message=f'File #{file_id} deleted')

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(media_library, url_prefix=config.get('general', 'urlprefix', fallback='/'))
