from app.models.menu import Menu, MenuItem
from app.utils.exceptions import AppError


class MenuService:
    def __init__(self, store, auth_service):
        self.__store = store
        self.__auth = auth_service
        self.__menu = Menu()
        self.notices = []
        for record in store.load():
            try:
                self.__menu.restore(MenuItem.from_dict(record))
            except AppError as error:
                self.notices.append(str(error))
        self.notices.extend(store.notices)

    def __save(self):
        self.__store.save([item.to_dict() for item in self.__menu.get_all_items()])

    def add_item(self, name, price, category):
        self.__auth.require("menu.edit")
        item = self.__menu.add_item(name, price, category)
        self.__save()
        return item

    def update_item(self, item_id, name=None, price=None, category=None):
        self.__auth.require("menu.edit")
        item = self.__menu.update_item(item_id, name, price, category)
        self.__save()
        return item

    def delete_item(self, item_id):
        self.__auth.require("menu.edit")
        item = self.__menu.delete_item(item_id)
        self.__save()
        return item

    def get_item(self, item_id):
        return self.__menu.get_item(item_id)

    def require_item(self, item_id):
        return self.__menu.require_item(item_id)

    def get_all_items(self):
        return self.__menu.get_all_items()

    def search_items(self, keyword):
        return self.__menu.search(keyword)

    def count(self):
        return len(self.__menu.get_all_items())
