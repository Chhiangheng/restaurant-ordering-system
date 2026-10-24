from app.models.user import ROLES, User
from app.storage.defaults import default_users
from app.utils import clock, rules, security
from app.utils.exceptions import (
    AppError,
    AuthenticationError,
    DuplicateError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


class AuthService:
    def __init__(self, store):
        self.__store = store
        self.__users = {}
        self.__current = None
        self.notices = []
        self.__load()

    def __load(self):
        for record in self.__store.load():
            try:
                user = User.from_dict(record)
            except AppError as error:
                self.notices.append(str(error))
                continue
            if user.user_id in self.__users or self.__find(user.username):
                self.notices.append(f"Duplicate user '{user.username}' was ignored.")
                continue
            self.__users[user.user_id] = user
        if not self.__users:
            self.notices.append("No valid users were found, default accounts were created.")
            for record in default_users():
                user = User.from_dict(record)
                self.__users[user.user_id] = user
            self.__save()
        self.notices.extend(self.__store.notices)

    def __save(self):
        self.__store.save([user.to_dict() for user in self.get_users_unchecked()])

    def get_users_unchecked(self):
        return [self.__users[key] for key in sorted(self.__users)]

    def __find(self, username):
        username = str(username).strip().lower()
        for user in self.__users.values():
            if user.username.lower() == username:
                return user
        return None

    def __next_id(self):
        return max(self.__users, default=0) + 1

    @property
    def current_user(self):
        return self.__current

    def count_users(self):
        return len(self.__users)

    def login(self, username, password):
        user = self.__find(username)
        if user is None or not security.verify_password(password, user.password_hash):
            raise AuthenticationError("Incorrect username or password.")
        if not user.active:
            raise AuthenticationError("This account is disabled. Contact an administrator.")
        user.last_login = clock.format_datetime(clock.now())
        self.__current = user
        self.__save()
        return user

    def logout(self):
        user = self.__current
        self.__current = None
        return user

    def can(self, permission):
        return self.__current is not None and self.__current.can(permission)

    def require(self, permission):
        if self.__current is None:
            raise PermissionDeniedError("Please log in first.")
        if not self.__current.can(permission):
            raise PermissionDeniedError("You do not have permission to perform this action.")

    def __admin_count(self, excluding=None):
        return sum(
            1 for user in self.__users.values()
            if user.role == "admin" and user.active and user is not excluding
        )

    def get_all_users(self):
        self.require("users")
        return self.get_users_unchecked()

    def require_user(self, user_id):
        self.require("users")
        user = self.__users.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} was not found.")
        return user

    def search_users(self, keyword):
        self.require("users")
        keyword = keyword.strip().lower()
        return [
            user for user in self.get_users_unchecked()
            if keyword == str(user.user_id)
            or keyword in user.username.lower()
            or keyword in user.full_name.lower()
            or keyword in user.role
        ]

    def add_user(self, username, password, role, full_name):
        self.require("users")
        username = rules.check_username(username)
        if self.__find(username):
            raise DuplicateError(f"Username '{username}' already exists.")
        security.validate_password(password)
        user = User(
            self.__next_id(),
            username,
            security.hash_password(password),
            role,
            full_name,
            True,
            clock.format_datetime(clock.now()),
            "",
        )
        self.__users[user.user_id] = user
        self.__save()
        return user

    def update_user(self, user_id, full_name=None, role=None, active=None):
        user = self.require_user(user_id)
        new_role = user.role if role is None else str(role).strip().lower()
        new_active = user.active if active is None else bool(active)
        if new_role not in ROLES:
            raise ValidationError("Role must be one of: " + ", ".join(ROLES))
        if user is self.__current and not new_active:
            raise ValidationError("You cannot disable your own account.")
        loses_admin = user.role == "admin" and user.active and (new_role != "admin" or not new_active)
        if loses_admin and self.__admin_count(excluding=user) == 0:
            raise ValidationError("At least one active admin account is required.")
        if full_name is not None:
            user.full_name = full_name
        user.role = new_role
        user.active = new_active
        self.__save()
        return user

    def reset_password(self, user_id, new_password):
        user = self.require_user(user_id)
        security.validate_password(new_password)
        user.password_hash = security.hash_password(new_password)
        self.__save()
        return user

    def change_own_password(self, old_password, new_password):
        user = self.__current
        if user is None:
            raise PermissionDeniedError("Please log in first.")
        if not security.verify_password(old_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect.")
        if old_password == new_password:
            raise ValidationError("The new password must be different from the current password.")
        security.validate_password(new_password)
        user.password_hash = security.hash_password(new_password)
        self.__save()

    def delete_user(self, user_id):
        user = self.require_user(user_id)
        if user is self.__current:
            raise ValidationError("You cannot delete the account you are using.")
        if user.role == "admin" and user.active and self.__admin_count(excluding=user) == 0:
            raise ValidationError("At least one active admin account is required.")
        del self.__users[user_id]
        self.__save()
        return user
