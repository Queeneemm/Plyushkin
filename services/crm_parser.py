from dataclasses import dataclass
from pathlib import Path

from openpyxl import load_workbook

from bot.utils.text import normalize_name


@dataclass(slots=True)
class CRMParserConfig:
    name_column: str
    stock_column: str
    header_row: int = 1
    sheet_name: str | None = None


class CRMExcelParser:
    def __init__(self, config: CRMParserConfig):
        self.config = config

    def _get_headers_map(self, row) -> dict[str, int]:
        mapping = {}
        for idx, cell in enumerate(row, start=1):
            if cell.value:
                mapping[normalize_name(str(cell.value)).lower()] = idx
        return mapping

    def parse_stock(self, file_path: str | Path) -> dict[str, float]:
        wb = load_workbook(file_path, data_only=True)
        ws = wb[self.config.sheet_name] if self.config.sheet_name and self.config.sheet_name in wb.sheetnames else wb.active

        header_cells = next(ws.iter_rows(min_row=self.config.header_row, max_row=self.config.header_row))
        header_map = self._get_headers_map(header_cells)

        name_idx = header_map.get(self.config.name_column.lower())
        stock_idx = header_map.get(self.config.stock_column.lower())
        if not name_idx or not stock_idx:
            raise ValueError('Не найдены требуемые колонки в CRM файле')

        result: dict[str, float] = {}
        for row in ws.iter_rows(min_row=self.config.header_row + 1):
            raw_name = row[name_idx - 1].value
            raw_stock = row[stock_idx - 1].value
            if raw_name is None:
                continue
            name = normalize_name(str(raw_name))
            if not name:
                continue
            try:
                stock = float(raw_stock or 0)
            except (TypeError, ValueError):
                stock = 0
            result[name] = stock

        return result
