import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Стандартный logging в stdout — контейнер сам собирает stdout как логи
    (docker logs / journald / любой лог-агрегатор), отдельного файлового
    логирования на этом масштабе не нужно.
    """
    root = logging.getLogger()
    if root.handlers:
        return  # уже настроено (например, повторный импорт в тестах)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root.addHandler(handler)
    root.setLevel(settings.log_level)
