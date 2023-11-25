from grubstack import gsdb

# Stores
def getStoreMenus(store_id: int):
  return gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url, label_color
                                    FROM gs_menu c INNER JOIN gs_store_menu p ON p.menu_id = c.menu_id 
                                    WHERE p.store_id = %s ORDER BY name ASC""", (store_id,))
def deleteStore(store_id: int):
  return gsdb.execute("DELETE FROM gs_store WHERE store_id = %s", (store_id,))

# Menus
def getMenuItems(menu_id: int):
  return gsdb.fetchall("""SELECT c.item_id, name, description, thumbnail_url, label_color, price, sale_price, is_onsale
                      FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                      WHERE p.menu_id = %s ORDER BY name ASC""", (menu_id,))

def deleteMenu(menu_id: int):
  return gsdb.execute("DELETE FROM gs_menu WHERE menu_id = %s", (menu_id,))
