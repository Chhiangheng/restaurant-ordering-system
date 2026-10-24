import json
import os
import tempfile
from pathlib import Path

from app.utils.exceptions import DataFileError


class JsonStore:
    def __init__(self, path, default):
        self.__path = Path(path)
        self.__default = default
        self.notices = []

    @property
    def path(self):
        return self.__path

    def load(self):
        name = self.__path.name
        if not self.__path.exists():
            self.notices.append(f"{name} was not found, a new file was created")
            data = self.__default()
            self.save(data)
            return data
        try:
            with open(self.__path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            backup = self.__path.with_name(name + ".bak")
            try:
                os.replace(self.__path, backup)
            except OSError as error:
                raise DataFileError(f"{name} is damaged and cannot be moved: {error}")
            self.notices.append(f"{name} was damaged, it was saved as {backup.name} and a new file was created")
            data = self.__default()
            self.save(data)
            return data
        except OSError as error:
            raise DataFileError(f"Cannot read {name}: {error}")

    def save(self, data):
        try:
            self.__path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temp_path = tempfile.mkstemp(dir=str(self.__path.parent), suffix=".tmp")
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
            os.chmod(temp_path, 0o644)
            os.replace(temp_path, self.__path)
        except OSError as error:
            raise DataFileError(f"Cannot save {self.__path.name}: {error}")
