import os
from abc import ABC, abstractmethod

class StorageService(ABC):
    @abstractmethod
    def save(self, filename: str, content: bytes) -> str:
        pass

class LocalStorageService(StorageService):
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save(self, filename: str, content: bytes) -> str:
        file_path = os.path.join(self.base_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path

storage_service = LocalStorageService()