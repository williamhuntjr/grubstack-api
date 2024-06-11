from grubstack import gsdb

# Stores
def getRestaurantMenus(restaurant_id: int):
  return gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url
                                    FROM gs_menu c INNER JOIN gs_restaurant_menu p ON p.menu_id = c.menu_id 
                                    WHERE p.restaurant_id = %s ORDER BY name ASC""", (restaurant_id,))
def deleteRestaurant(restaurant_id: int):
  return gsdb.execute("DELETE FROM gs_restaurant WHERE restaurant_id = %s", (restaurant_id,))

# Menus
def getMenuItems(menu_id: int):
  return gsdb.fetchall("""SELECT c.item_id, name, description, thumbnail_url, price, sale_price, is_onsale
                      FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                      WHERE p.menu_id = %s ORDER BY name ASC""", (restaurant_id,))

def deleteMenu(menu_id: int):
  return gsdb.execute("DELETE FROM gs_menu WHERE menu_id = %s", (restaurant_id,))
