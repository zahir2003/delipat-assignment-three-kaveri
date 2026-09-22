"""Small ClickUp API client wrapper.

Token is loaded from environment variables and must never be hard-coded.
Implementation will be expanded as the ClickUp workspace IDs become known.
"""

import os
from typing import Any

import requests


class ClickUpClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("CLICKUP_API_TOKEN")
        if not self.token:
            raise ValueError("CLICKUP_API_TOKEN is not configured")
        self.base_url = "https://api.clickup.com/api/v2"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": self.token})

    def get(self, path: str, **kwargs: Any) -> Any:
        response = self.session.get(f"{self.base_url}{path}", timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, **kwargs: Any) -> Any:
        response = self.session.post(f"{self.base_url}{path}", timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
