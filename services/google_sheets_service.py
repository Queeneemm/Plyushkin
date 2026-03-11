from datetime import datetime

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class GoogleSheetsService:
    def __init__(self, credentials_json: str, spreadsheet_id: str, template_sheet_name: str):
        creds = Credentials.from_service_account_file(credentials_json, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        self.service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        self.spreadsheet_id = spreadsheet_id
        self.template_sheet_name = template_sheet_name

    def _sheet_by_name(self, name: str) -> dict:
        meta = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        for sh in meta.get('sheets', []):
            if sh.get('properties', {}).get('title') == name:
                return sh
        raise ValueError(f'Sheet {name} not found')

    def create_inventory_sheet(self) -> tuple[int, str, str]:
        template_sheet = self._sheet_by_name(self.template_sheet_name)
        template_id = template_sheet['properties']['sheetId']
        copied = self.service.spreadsheets().sheets().copyTo(
            spreadsheetId=self.spreadsheet_id,
            sheetId=template_id,
            body={'destinationSpreadsheetId': self.spreadsheet_id},
        ).execute()
        new_sheet_id = copied['sheetId']
        tab_name = f"Инвентарка {datetime.now().strftime('%Y-%m-%d %H-%M')}"
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': [{'updateSheetProperties': {'properties': {'sheetId': new_sheet_id, 'title': tab_name}, 'fields': 'title'}}]},
        ).execute()
        url = f'https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit#gid={new_sheet_id}'
        return new_sheet_id, tab_name, url

    def write_inventory_rows(self, tab_name: str, rows: list[tuple[str, float, float]]) -> None:
        start = 3
        a_values = [[r[0]] for r in rows]
        c_values = [[r[1]] for r in rows]
        d_values = [[r[2]] for r in rows]
        end = start + len(rows) - 1
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {'range': f"'{tab_name}'!A{start}:A{end}", 'values': a_values},
                {'range': f"'{tab_name}'!C{start}:C{end}", 'values': c_values},
                {'range': f"'{tab_name}'!D{start}:D{end}", 'values': d_values},
            ],
        }
        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()

    def read_cell(self, tab_name: str, cell: str) -> str:
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{tab_name}'!{cell}",
        ).execute()
        values = result.get('values', [])
        if not values or not values[0]:
            return ''
        return str(values[0][0]).strip()
