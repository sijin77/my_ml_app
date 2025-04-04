import bcrypt


def get_password_hash(password: str) -> str:
    # Хеширует пароль с использованием bcrypt
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Сравнивает введенный пароль с хешем
    try:
        # Преобразуем оба пароля в байты
        plain_password_bytes = plain_password.encode("utf-8")
        hashed_password_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except (ValueError, AttributeError):
        # Обрабатываем случаи, когда hashed_password невалиден
        return False
