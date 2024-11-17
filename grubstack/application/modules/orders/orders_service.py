from grubstack.application.modules.locations.locations_service import LocationService
from grubstack.application.modules.products.menus.menus_service import MenuService

location_service = LocationService()
menu_service = MenuService()

class ValidationError(Exception):
  def __init__(self, error, status_code):
    self.error = error
    self.status_code = status_code

class OrderService:
  def __init__(self):
    pass

  def validate_cart(self, location_id: int, cart_items: list):
    for item in cart_items:
      menu_exists = location_service.menu_exists(location_id, item['menu_id'])
      if menu_exists is False:
        raise ValidationError({ "code": "invalid_menu",
                  "description":"The specified menu does not exist on the location." }, 404)
      else:
        item_exists = menu_service.item_exists(item['menu_id'], item['item_id'])
        if item_exists is False:
          raise ValidationError({ "code": "invalid_item",
                    "description":"The specified item does not exist on the menu." }, 404)