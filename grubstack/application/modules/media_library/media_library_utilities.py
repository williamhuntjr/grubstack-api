ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_file_data(file_data: dict, filters: dict = {}):
  json_data = {
    "id": file_data['file_id'],
    "name": file_data['file_name'],
    "file_size": file_data['file_size'],
    "file_type": file_data['file_type'],
    "url": file_data['file_name']
  }

  return json_data
  