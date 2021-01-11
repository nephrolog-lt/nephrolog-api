from unidecode import unidecode


def str_to_ascii(s: str) -> str:
    return unidecode(s)
