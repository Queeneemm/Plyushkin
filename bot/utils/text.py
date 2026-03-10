import re


def normalize_name(value: str) -> str:
    return re.sub(r'\s+', ' ', value.replace('\n', ' ').strip())


def parse_aliases(raw: str) -> list[str]:
    aliases = [normalize_name(part).lower() for part in raw.split(',')]
    return [a for a in aliases if a]
