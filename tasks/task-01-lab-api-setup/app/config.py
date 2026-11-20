"""
LedgerPro Accountants - Lab API Configuration
Environment and runtime settings for the Accounting Lab API.
"""

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "LedgerPro Accountants - Lab API"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    environment: str = "development-lab"
    default_currency: str = "USD"
    tax_rate_standard: float = 0.0825  # 8.25% standard corporate tax rate


settings = Settings()
