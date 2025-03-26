from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from url_shortener.config import LIFETIME


class CreateURL(BaseModel):
    url: str
    lifetime: int = LIFETIME
    alias: Optional[str] = None
    project_name: Optional[str] = None


class UpdateURL(BaseModel):
    update_url: str


class URLStatistics(BaseModel):
    url: str
    created_at: datetime
    clicks_count: int
    last_clicked_at: Optional[datetime]
