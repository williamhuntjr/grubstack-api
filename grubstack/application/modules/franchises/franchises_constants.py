from grubstack import app

PER_PAGE = app.config['PER_PAGE']
FRANCHISE_FILTERS = ['showStores', 'showMenus']

DEFAULT_FILTERS = {
  "showStores": True,
  "showMenus": True,
}