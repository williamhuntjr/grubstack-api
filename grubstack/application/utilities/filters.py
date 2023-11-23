def generateFilters(filterList: list, requestArgs):
  filters = {}

  for franchise_filter in filterList:
    if requestArgs.get(franchise_filter):
      filters[franchise_filter] = requestArgs.get(franchise_filter)
  return filters