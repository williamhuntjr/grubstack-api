import logging, os
import psycopg2
import psycopg2.extras
from flask import current_app

logger = logging.getLogger("grubstack")

class GrubDatabase(object):
  def __init__(self, config, server=None, database=None, port=None, user=None, password=None, ssl=None):
    self.config     = config
    self.server     = server   or os.environ.get('DATABASE_HOST')
    self.database   = database or os.environ.get('DATABASE_NAME')
    self.port       = port     or os.environ.get('DATABASE_PORT')
    self.user       = user     or os.environ.get('DATABASE_USER')
    self.password   = password or os.environ.get('DATABASE_PASSWORD')
    self.ssl        = ssl      or os.environ.get('DATABASE_SSL')
    self.connection = self.connect()

  def connect(self):
    try:
      con = psycopg2.connect(host=self.server,
                             database=self.database,
                             user=self.user,
                             password=self.password,
                             port=self.port,
                             sslmode=self.ssl,
                             connect_timeout=15)
      con.autocommit = True

    except Exception as e:
      logger.exception(e)
      return None

    finally:
      return con

  def reconnect(self):
    del self.connection
    self.connection = self.connect()

  def get_cursor(self):
    try:
      cur = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
      if cur is not None:
        return cur
      else:
        self.reconnect()
        return None

    except Exception as e:
      print(e)
      return None

  def test_connection(self):
    try:
      if not self.connection or self.connection.closed != 0:
        self.reconnect()
    except Exception as e:
      print(e)
      pass

  def fetchone(self, query, params=None):
    try:
      cur = self.get_cursor()
      if cur is not None:
        cur.execute("SET app.tenant_id = %s", (current_app.config.get('TENANT_ID'),))
        cur.execute(query, params)
        row = cur.fetchone()
        cur.close()
        return row
      else:
        self.reconnect()
        return None

    except Exception as e:
      logger.exception(e)
      return None

    finally:
      if cur is not None:
        cur.close()
        del cur

  def fetchall(self, query, params=None):
    try:
      cur = self.get_cursor()
      if cur is not None:
        cur.execute("SET app.tenant_id = %s", (current_app.config.get('TENANT_ID'),))
        cur.execute(query, params)
        return cur.fetchall()
      else:
        self.reconnect()
        return None

    except Exception as e:
      logger.exception(e)
      return None

    finally:
      if cur is not None:
        cur.close()
        del cur

  def execute(self, query, params=None):
    try:
      cur = self.get_cursor()
      if cur is not None:
        cur.execute("SET app.tenant_id = %s", (current_app.config.get('TENANT_ID'),))
        return cur.execute(query, params)
      else:
        self.reconnect()
        return None

    except Exception as e:
      logger.exception(e)
      return None

    finally:
      if cur is not None:
        cur.close()
        del cur

