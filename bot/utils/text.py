import re


def normalize_name(value: str) -> str:
    return re.sub(r'\s+', ' ', value.replace('\n', ' ').strip())


def parse_aliases(raw: str) -> list[str]:
    aliases = [normalize_name(part).lower() for part in raw.split(',')]
    return [a for a in aliases if a]


def parse_ids(raw: str) -> list[int]:
    ids: list[int] = []
    for part in raw.split(','):
        value = normalize_name(part)
        if not value or not value.isdigit():
            return []
        ids.append(int(value))
    return ids
