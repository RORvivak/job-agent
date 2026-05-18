from abc import ABC, abstractmethod
from typing import Any


class ApplyResult:
    def __init__(self, success: bool = False, external_url: str = "",
                 error: str = "", screenshot_path: str = ""):
        self.success = success
        self.external_url = external_url
        self.error = error
        self.screenshot_path = screenshot_path

    def is_external(self) -> bool:
        return bool(self.external_url)


class BasePortal(ABC):
    name: str = "base"

    @abstractmethod
    async def login(self, page, creds: dict) -> bool: ...

    @abstractmethod
    async def search(self, page, prefs: dict, limit: int = 10) -> list[dict]: ...

    @abstractmethod
    async def apply(self, page, job: dict, resume_path: str,
                    cover_letter_path: str, candidate: dict) -> ApplyResult: ...
