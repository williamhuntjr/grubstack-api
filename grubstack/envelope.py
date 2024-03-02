import json
from enum import Enum

class GStatusCode(Enum):
  SUCCESS = 'success'
  WARNING = 'warning'
  ERROR   = 'error'
  UNKNOWN = 'unknown'

  def __str__(self):
    return self.value

class GStatus(dict):
  def __init__(self, code=GStatusCode.SUCCESS, message=str(), totalrowcount=0, totalpages=0):
    dict.__init__(self)
    self['code'] = code
    if message != '':
      self['message'] = message
    if totalrowcount != 0: 
      self['totalrowcount'] = totalrowcount
    if totalpages != 0: 
      self['totalpages'] = totalpages

class GRequest(dict):
  def __init__(self, data=None, options=dict()):
    dict.__init__(self)
    self['data'] = data
    self['options'] = options

  def __str__(self):
    return self.tojson()

  def tojson(self):
    return json.dumps(self, indent=2, default=str)

  @staticmethod
  def fromjson(pjson):
    pdict = json.loads(pjson)
    if 'data' not in pdict:
      raise ValueError('Missing data object')
    if type(pdict['data']) != type(dict()) and type(pdict['data']) != type(list()):
      raise TypeError('Invalid request object. Must be a JSON Object or Array')
    return GRequest(
      pdict['data'],
      pdict.get('options')
    )

class GResponse(dict):
  def __init__(self, data=str(), message=str(), status=GStatusCode.SUCCESS, totalrowcount=0, totalpages=0, hasMore=False):
    dict.__init__(self)
    self['data'] = data
    if hasMore is not False: self['hasMore'] = True
    if totalrowcount > 0 and totalpages > 0: self['status'] = GStatus(status, message, totalrowcount, totalpages)
    else: self['status'] = GStatus(status, message)

  def __str__(self):
    return self.tojson()

  def tojson(self):
    return json.dumps(self, indent=2, default=str)

  @staticmethod
  def fromjson(pjson):
    pdict = json.loads(pjson)
    if 'data' not in pdict:
      raise ValueError('Missing data object')
    if 'status' not in pdict:
      raise ValueError('Missing status object')

    return GResponse(
      pdict['data'],
      pdict['status']['message'],
      GStatusCode[pdict['status']['code'].upper()],
      pdict['status']['totalrowcount'],
      pdict['status']['totalpages']
    )