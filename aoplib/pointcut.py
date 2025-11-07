from abc import ABC, abstractmethod
import fnmatch
from typing import Callable


class IJoinFilter(ABC):
    @abstractmethod
    def filter(self, method, meta: dict):
        pass


class NameFilter(IJoinFilter):
    def __init__(
        self, *names
    ) -> None:
        self.names = []
        self.patterns = []
        for name in names:
            if "*" in name or "?" in name:
                self.patterns.append(name)
            else:
                self.names.append(name)

    def filter(self, method: Callable, meta: dict):
        name = method.__qualname__
        short_name = meta.get("name") or method.__name__
        if name in self.names:
            return True
        if short_name in self.names:
            return True
        for pattern in self.patterns:
            if fnmatch(name, pattern):
                return True
            if fnmatch(short_name, pattern):
                return True
        return False


def with_name(*names: str) -> IJoinFilter:
    return NameFilter(*names)


class TagFilter(IJoinFilter):
    def __init__(self, *tags) -> None:
        self.tags = tags

    def filter(self, method: Callable, meta: dict):
        tags = meta.get("tags")
        if tags is None:
            return False
        return any(tag in tags for tag in self.tags)


def with_tag(*tags: str) -> IJoinFilter:
    return TagFilter(*tags)
