from grubstack import gsdb

def getFranchiseStores(franchise_id: int):
   return gsdb.fetchall("""SELECT c.store_id, name, address1, city, state, postal, store_type, thumbnail_url, phone_number
                            FROM gs_store c INNER JOIN gs_franchise_store p ON p.store_id = c.store_id 
                            WHERE p.franchise_id = %s ORDER BY name ASC""", (franchise_id,))

def getStoreMenus(store_id: int):
  return gsdb.fetchall("""SELECT c.menu_id, name, description, thumbnail_url, label_color
                                    FROM gs_menu c INNER JOIN gs_store_menu p ON p.menu_id = c.menu_id 
                                    WHERE p.store_id = %s ORDER BY name ASC""", (store_id,))

def getMenuItems(menu_id: int):
  return gsdb.fetchall("""SELECT c.item_id, name, description, thumbnail_url, label_color, price, sale_price, is_onsale
                      FROM gs_item c INNER JOIN gs_menu_item p ON p.item_id = c.item_id 
                      WHERE p.menu_id = %s ORDER BY name ASC""", (menu_id,))
