"""Small ClickUp API client wrapper.

Token is loaded from environment variables and must never be hard-coded.
"""

import os
from typing import Any

import requests


class ClickUpClient:
    """Minimal ClickUp API v2 client."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("CLICKUP_API_TOKEN")

        if not self.token:
            raise ValueError("CLICKUP_API_TOKEN is not configured")

        self.base_url = "https://api.clickup.com/api/v2"

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": self.token,
                "Content-Type": "application/json",
            }
        )

    def get(self, path: str, **kwargs: Any) -> Any:
        """Send a GET request to ClickUp."""
        response = self.session.get(
            f"{self.base_url}{path}",
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def post(self, path: str, **kwargs: Any) -> Any:
        """Send a POST request to ClickUp."""
        response = self.session.post(
            f"{self.base_url}{path}",
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def get_workspaces(self) -> Any:
        """Return ClickUp workspaces available to this token."""
        return self.get("/team")

    def get_spaces(self, workspace_id: str) -> Any:
        """Return Spaces in a ClickUp workspace."""
        return self.get(f"/team/{workspace_id}/space")

    def get_folders(self, space_id: str) -> Any:
        """Return Folders in a ClickUp Space."""
        return self.get(f"/space/{space_id}/folder")

    def get_space_lists(self, space_id: str) -> Any:
        """Return Lists directly inside a ClickUp Space."""
        return self.get(f"/space/{space_id}/list")

    def get_list(self, list_id: str) -> Any:
        """Return details for a ClickUp List."""
        return self.get(f"/list/{list_id}")

    def get_list_tasks(self, list_id: str) -> Any:
        """Return tasks currently in a ClickUp List."""
        return self.get(f"/list/{list_id}/task")