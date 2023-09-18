import logging, os, subprocess, json
from datetime import datetime
from math import ceil
from flask import Blueprint, request
from werkzeug.utils import secure_filename
from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission
from .media_library_utilities import allowed_file

media_library = Blueprint('media_library', __name__)
logger = logging.getLogger('grubstack')

UPLOAD_FOLDER = '/uploads/' + app.config['TENANT_ID']
PER_PAGE = 30

@media_library.route('/media-library', methods=['GET'])
@requires_auth
@requires_permission('ViewMediaLibrary')
def get_all():
  try:
    json_data = []
    files = gsdb.fetchall("SELECT * FROM gs_media_library")
    
    # Get route parameters
    page = request.args.get('page')
    limit = request.args.get('limit')

    if limit is None: limit = PER_PAGE
    else: limit = int(limit)

    if page is None: page = 1
    else: page = int(page)

    files_list = []
    for file in files:
      files_list.append({
        "id": file['file_id'],
        "name": file['file_name'],
        "file_type": file['file_type'],
        "file_size": file['file_size'],
      })

    # Calculate paged data
    offset = page - 1
    start = offset * limit
    end = start + limit
    total_pages = ceil(len(files) / limit)

    # Get paged data
    json_data = files_list[start:end]

    return gs_make_response(data=json_data, totalrowcount=len(files), totalpages=total_pages)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve files. Please try again',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@media_library.route('/media-library/upload', methods=['POST'])
@requires_auth
@requires_permission('MaintainMediaLibrary')
def upload_file():
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
      if os.path.exists(UPLOAD_FOLDER) == False:
        os.mkdir(UPLOAD_FOLDER) 

      now = datetime.now()
      timestamp = now.strftime("-%m_%d_%Y_%H:%M:%S")

      filename = secure_filename(file.filename)
      formatted_filename = os.path.splitext(filename)[0] + timestamp + os.path.splitext(filename)[1]

      full_path = os.path.join(UPLOAD_FOLDER, formatted_filename)

      file.save(os.path.join(full_path))

      get_mime = subprocess.run(["file", "-b", "--mime-type", full_path], capture_output=True)
      file_type = get_mime.stdout.decode("utf-8").rstrip()
      file_size = os.path.getsize(full_path)

      gsdb.execute("INSERT INTO gs_media_library (tenant_id, file_id, file_name, file_size, file_type) VALUES (%s, DEFAULT, %s, %s, %s)", (app.config['TENANT_ID'], formatted_filename, file_size, file_type,))
      return gs_make_response(message='File uploaded successfully',
                      status=GStatusCode.SUCCESS,
                      httpstatus=200)
  
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to upload file',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@media_library.route('/media-library/delete', methods=['POST'])
@requires_auth
@requires_permission("MaintainMediaLibrary")
def delete_file():
  try:
    json_data = {}
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      file_id = params['file_id']
      if file_id:
        # Check if exists
        row = gsdb.fetchone("SELECT * FROM gs_media_library WHERE file_id = %s", (file_id,))
        if row is None:
          return gs_make_response(message='Invalid file',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)
        else:
          full_path = os.path.join(UPLOAD_FOLDER, row['file_name'])
          if full_path != '/':
            print("deleting " + full_path)
            os.remove(full_path)
          qry = gsdb.execute("DELETE FROM gs_media_library WHERE file_id = %s", (file_id,))
          return gs_make_response(message=f'File #{file_id} deleted')
          
      else:
        return gs_make_response(message='Invalid data',
                                status=GStatusCode.ERROR,
                                httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(media_library, url_prefix=config.get('general', 'urlprefix', fallback='/'))
