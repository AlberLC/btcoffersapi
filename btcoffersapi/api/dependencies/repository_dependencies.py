from collections.abc import Callable

from database.repositories.repository import Repository


def get_repository[T:Repository](repository_class: type[T]) -> Callable[[], T]:
    def wrapper() -> T:
        return repository_class()

    return wrapper
