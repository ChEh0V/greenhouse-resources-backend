"""Текущий пользователь до появления авторизации (лабораторная №3).

Создатель ресурсов зафиксирован константой. Класс-одиночка гарантирует,
что во всех методах используется один и тот же объект пользователя."""

CREATOR_USER_ID = 2  # chekhovich


class CurrentUser:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.user_id = CREATOR_USER_ID
        return cls._instance


def get_current_user_id() -> int:
    """Функция-singleton: всегда возвращает ид одного и того же создателя."""
    return CurrentUser().user_id
