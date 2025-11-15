from passlib.context import CryptContext  # type: ignore

# Контекст для хеширования паролей.
# Используем алгоритм sha256_crypt, который является рекомендуемым для хеширования паролей.
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли введенный пароль хешированному.

    Args:
        plain_password (str): Пароль, введенный пользователем.
        hashed_password (str): Хешированный пароль из базы данных.

    Returns:
        bool: True, если пароли совпадают, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Хеширует пароль.

    Args:
        password (str): Пароль в открытом виде.

    Returns:
        str: Хешированный пароль.
    """
    return pwd_context.hash(password)
