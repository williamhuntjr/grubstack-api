from math import ceil

from grubstack import app

PER_PAGE = app.config['PER_PAGE']

def generate_filters(filterList: list, request_args):
  filters = {}

  for franchise_filter in filterList:
    if request_args.get(franchise_filter):
      filters[franchise_filter] = request_args.get(franchise_filter)
  return filters

def create_pagination_params(request_args):
  # Get route parameters
  page = request_args.get('page')
  limit = request_args.get('limit')

  if limit is None: limit = PER_PAGE
  else: limit = int(limit)

  if page is None: page = 1
  else: page = int(page)

  return page, limit

def generate_paginated_data(data, page, limit):
  # Calculate paged data
  offset = page - 1
  start = offset * limit
  end = start + limit
  total_pages = ceil(len(data) / limit)
  total_rows = len(data)
  
  # Get paged data
  json_data = data[start:end]

  return (json_data, total_rows, total_pages)