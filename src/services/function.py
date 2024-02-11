def some_short_id_generation_function(url_id: int) -> str:
    """Функция для сокращения URL."""
    short_id = hex(url_id)[2:]

    return short_id
