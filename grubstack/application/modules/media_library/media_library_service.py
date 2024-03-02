import os, subprocess

from datetime import datetime

from pypika import Query, Table
from werkzeug.utils import secure_filename

from grubstack import app, gsdb

from grubstack.application.utilities.filters import generate_paginated_data

from .media_library_constants import PER_PAGE, UPLOAD_FOLDER
from .media_library_utilities import format_file_data

class MediaLibraryService:
  def __init__(self):
    pass

  def get_all(self, page: int = 1, limit: int = PER_PAGE):
    gs_media_library = Table('gs_media_library')
    qry = Query.from_(
      gs_media_library
    ).select(
      gs_media_library.file_id,
      gs_media_library.file_name,
      gs_media_library.file_size,
      gs_media_library.file_type,
    )
    
    media_library_files = gsdb.fetchall(str(qry))
    
    filtered = []
    for file in media_library_files:
      filtered.append(format_file_data(file))

    json_data, total_rows, total_pages = generate_paginated_data(filtered, page, limit)

    return (json_data, total_rows, total_pages)
  
  def get(self, file_id: int):
    gs_media_library = Table('gs_media_library')

    qry = Query.from_(
      gs_media_library
    ).select(
      gs_media_library.file_id,
      gs_media_library.file_name,
      gs_media_library.file_size,
      gs_media_library.file_type,
    ).where(
      gs_media_library.file_id == file_id
    )

    file = gsdb.fetchone(str(qry))

    if file is not None:
      return format_file_data(file)
    else:
      return None

  def upload(self, file):
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

    gs_media_library = Table('gs_media_library')
    qry = Query.into(
      gs_media_library
    ).columns(
      gs_media_library.tenant_id,
      gs_media_library.file_name,
      gs_media_library.file_size,
      gs_media_library.file_type
    ).insert(
      app.config['TENANT_ID'],
      formatted_filename,
      file_size,
      file_type
    )
    gsdb.execute(str(qry))

  def delete(self, file_id: int):
    file_data = self.get(file_id)

    full_path = os.path.join(UPLOAD_FOLDER, file_data['name'])
    if full_path != '/':
      os.remove(full_path)

    gs_media_library = Table('gs_media_library')

    qry = Query.from_(
      gs_media_library
    ).delete().where(
      gs_media_library.file_id == file_data['id']
    ).where(
      gs_media_library.tenant_id == app.config['TENANT_ID']
    )

    qry = gsdb.execute(str(qry))