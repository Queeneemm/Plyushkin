from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    bot_token: str = Field(alias='BOT_TOKEN')
    database_url: str = Field(default='sqlite+aiosqlite:///./inventory_bot.db', alias='DATABASE_URL')
    admin_telegram_id: int = Field(alias='ADMIN_TELEGRAM_ID')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')

    google_credentials_json: str = Field(alias='GOOGLE_CREDENTIALS_JSON')
    google_spreadsheet_id: str = Field(alias='GOOGLE_SPREADSHEET_ID')
    template_sheet_name: str = Field(default='Шаблон', alias='TEMPLATE_SHEET_NAME')

    crm_name_column: str = Field(default='Наименование', alias='CRM_NAME_COLUMN')
    crm_stock_column: str = Field(default='Остаток', alias='CRM_STOCK_COLUMN')
    crm_header_row: int = Field(default=1, alias='CRM_HEADER_ROW')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
