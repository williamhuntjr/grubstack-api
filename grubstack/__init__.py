#!/usr/bin/env python
__version__ = '0.2.0'
import logging, configparser, os, sys, argparse
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pathlib import Path
from logging.handlers import RotatingFileHandler

from .database import GrubDatabase

config = configparser.RawConfigParser()
configfile = os.path.dirname(os.path.realpath(__file__)) + '/grubstack.ini'

load_dotenv()

if len(sys.argv) > 1:
  parser = argparse.ArgumentParser()
  parser.add_argument('-c', '--config', dest='config', help='full path to GrubStack API config file')
  args, extra = parser.parse_known_args()
  if args.config is not None:
    configfile = args.config
    print('INFO: Using config file from command line argument.')
    
elif os.environ.get('GRUBSTACK_CONFIG_FILE') is not None:
  configfile = os.environ.get('GRUBSTACK_CONFIG_FILE')
  print('INFO: Using config file from environment variable.')

tmpfile = Path(configfile)
if not tmpfile.exists():
  print('ERROR: Config file not found: {}'.format(configfile))
  sys.exit(-1)

print('INFO: Loading config from {}'.format(configfile))

config.read(configfile)
app = Flask(__name__)

if config.get('general', 'tenant_id', fallback='') != '':
  app.config['TENANT_ID']         = config.get('general', 'tenant_id', fallback='')
else:
  app.config['TENANT_ID']         = os.environ.get('TENANT_ID')

if config.get('general', 'access_token', fallback='') != '':
  app.config['ACCESS_TOKEN']         = config.get('general', 'access_token', fallback='')
else:
  app.config['ACCESS_TOKEN']         = os.environ.get('ACCESS_TOKEN')

# General settings
app.config['CONFIG_FILE']        = configfile
app.config['VERSION']            = __version__
app.config['DEBUG']              = config.getboolean('general', 'debug', fallback=False)
app.config['SECRET_KEY']         = config.get('general', 'secret')

# flask-limiter
app.config['RATELIMIT_ENABLED']         = config.getboolean('ratelimit', 'enabled', fallback=False)
app.config['RATELIMIT_DEFAULT']         = config.get('ratelimit', 'default_limit')
app.config['RATELIMIT_STRATEGY']        = config.get('ratelimit', 'strategy')
app.config['RATELIMIT_HEADERS_ENABLED'] = config.getboolean('ratelimit', 'headers_enabled')

# flask-mail
app.config['MAIL_ENABLED']        = os.environ.get('MAIL_EMAILED') or True
app.config['MAIL_SERVER']         = os.environ.get('MAIL_SERVER') or 'mail.grubstack.app'
app.config['MAIL_PORT']           = os.environ.get('MAIL_PORT') or '587'
app.config['MAIL_USE_TLS']        = os.environ.get('MAIL_USE_TLS') or True
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME') or 'api@grubstack.app'
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD') or 'grubstack'
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or 'GrubStack API <api@grubstack.app>'
app.config['MAIL_DEBUG']          = os.environ.get('MAIL_DEBUG') or False

# flask-jwt
app.config['JWT_SECRET_KEY'] = config.get('authentication', 'secret', fallback='secret')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.getint('authentication', 'access_token_expires', fallback=3600)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = config.getint('authentication', 'refresh_token_expires', fallback=2592000)
app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers', 'json']
app.config['JWT_COOKIE_DOMAIN'] = '.grubstack.app'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_SAMESITE'] = 'None'
app.config['JWT_ACCESS_COOKIE_NAME'] = '_grubstack_access_token'
app.config['JWT_REFRESH_COOKIE_NAME'] = '_grubstack_refresh_token'
app.config['SESSION_COOKIE_HTTPONLY'] = False
jwt = JWTManager(app)

# Initialize globals
mail = Mail(app)
gsdb = GrubDatabase(config)
gsprod = GrubDatabase(config, os.environ.get('DATABASE_HOST'), os.environ.get('CORPORATE_DB'))
cors = CORS(app, supports_credentials=True)

# API defaults
app.config['PER_PAGE'] = os.environ.get('MAIL_EMAILED') or 10
app.config['THUMBNAIL_PLACEHOLDER_IMG'] = '/assets/img/placeholder-image.jpg'
app.config['THUMBNAIL_PERSON_PLACEHOLDER_IMG'] = '/assets/img/placeholder-male.jpeg'

# Logger
from .loghandler import GrubStackLogHandler
logformatter = logging.Formatter(config.get('logging', 'log_format', 
                                            fallback='[%(asctime)s] [%(name)s] [%(levelname)s] [%(module)s/%(funcName)s/%(lineno)d] %(message)s'))
logformatter.default_msec_format = config.get('logging', 'log_msec_format', fallback='%s.%03d')

logger = logging.getLogger()
logger.setLevel(config.getint('logging', 'log_min_level', fallback=20))

# Child logger visibility
logger.propagate = True

# Logging type
if config.getboolean('logging', 'log_to_file', fallback=True):
  filehandler = RotatingFileHandler(config.get('logging', 'log_to_file_name', fallback='grubstack.log'), maxBytes=(1048576*5), backupCount=7)
  filehandler.setFormatter(logformatter)
  logger.addHandler(filehandler)

if config.getboolean('logging', 'log_to_console', fallback=True):
  consolehandler = logging.StreamHandler()
  consolehandler.setFormatter(logformatter)
  logger.addHandler(consolehandler)

if config.getboolean('logging', 'log_to_database', fallback=False):
  gshandler = GrubStackLogHandler()
  gshandler.setFormatter(logformatter)
  logger.addHandler(gshandler)

from . import grubstack
from . import authentication
from . import application
