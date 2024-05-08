from grubstack import app

PER_PAGE = app.config['PER_PAGE']
FRANCHISE_FILTERS = ['showRestaurants', 'showMenus']

DEFAULT_FILTERS = {
  "showRestaurants": True,
  "showMenus": True,
}