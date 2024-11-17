from grubstack import app

import cryptocode

def encrypt(value: str):
  salt = app.config['SQUARE_SALT_KEY']
  return cryptocode.encrypt(value, salt)

def decrypt(value: str):
  salt = app.config['SQUARE_SALT_KEY']
  return cryptocode.decrypt(value, salt)
