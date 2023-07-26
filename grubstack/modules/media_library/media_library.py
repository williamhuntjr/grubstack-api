import logging, os, subprocess
from datetime import datetime
from math import ceil
from flask import Blueprint, request
from werkzeug.utils import secure_filename

from grubstack import app, config, gsdb

from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode
from grubstack.authentication import requires_auth, requires_permission

media_library = Blueprint('media_library', __name__)
logger = logging.getLogger('grubstack')

UPLOAD_FOLDER = '/uploads/' + app.config['TENANT_ID']
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

per_page = 30

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    if limit is None: limit = per_page
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

  return gs_make_response(data=[])

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
      timestamp = now.strftime("-%d_%m_%Y_%H:%M:%S")

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
                            
app.register_blueprint(media_library, url_prefix=config.get('general', 'urlprefix', fallback='/'))
