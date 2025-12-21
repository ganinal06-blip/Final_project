from typing import List

# Функция для разбора .txt файла с разрешёнными пользователями
def parse_allowed_file_bytes(content: bytes) -> List[str]:
    text = content.decode(errors="ignore")
    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    for ln in lines:
        if not ln:
            continue
        # Если строка — ссылка, достаём только имя пользователя
        if ln.startswith("http://") or ln.startswith("https://"):
            parts = ln.rstrip("/").split("/")
            ln = parts[-1]
        ln = ln.strip()
        if not ln:
            continue
        cleaned.append(ln)
    return cleaned