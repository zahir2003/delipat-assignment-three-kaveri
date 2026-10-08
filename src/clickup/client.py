"""
This file provides the shared ClickUp API client used by project synchronization scripts.
We need it to keep authentication, request timeouts, and HTTP error handling consistent in one place.
"""

"""Small ClickUp API client wrapper.

Token is loaded from environment variables and must never be hard-coded.
"""

import os
from typing import Any

import requests


class ClickUpClient:
    """
    Sets up authentication and a reusable session so all ClickUp requests share the same settings.
    """

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

    """
    Sends a GET request and checks for API errors so callers receive validated response data.
    """

    def get(self, path: str, **kwargs: Any) -> Any:
        response = self.session.get(
            f"{self.base_url}{path}",
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    """
    Sends a POST request so callers can create ClickUp resources through the shared session.
    """

    def post(self, path: str, **kwargs: Any) -> Any:
        response = self.session.post(
            f"{self.base_url}{path}",
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    """
    Sends a DELETE request and handles empty responses so resource removal works consistently.
    """

    def delete(self, path: str, **kwargs: Any) -> Any:
        response = self.session.delete(
            f"{self.base_url}{path}",
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()

        if not response.content:
            return None

        return response.json()

    """
    Sends a PUT request and checks the response so callers can update ClickUp resources reliably.
    """

    def put(self, path: str, **kwargs: Any) -> Any:
        response = self.session.put(
            f"{self.base_url}{path}",
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Workspace discovery
    # ------------------------------------------------------------------

    """
    Lists available workspaces so setup scripts can find the intended project area.
    """

    def get_workspaces(self) -> Any:
        return self.get("/team")

    """
    Lists a workspace's spaces so callers can locate the project area for its lists.
    """

    def get_spaces(self, workspace_id: str) -> Any:
        return self.get(f"/team/{workspace_id}/space")

    """
    Lists folders in a space so integrations can inspect its existing organization.
    """

    def get_folders(self, space_id: str) -> Any:
        return self.get(f"/space/{space_id}/folder")

    """
    Lists lists in a space so setup code can reuse existing project lists.
    """

    def get_space_lists(self, space_id: str) -> Any:
        return self.get(f"/space/{space_id}/list")

    """
    Fetches one list so callers can inspect its current settings before using it.
    """

    def get_list(self, list_id: str) -> Any:
        return self.get(f"/list/{list_id}")

    """
    Fetches tasks from a list so importers can compare ClickUp records with their source data.
    """

    def get_list_tasks(
        self,
        list_id: str,
        subtasks: bool = False,
    ) -> Any:
        params = {
            "subtasks": str(subtasks).lower(),
        }

        return self.get(
            f"/list/{list_id}/task",
            params=params,
        )

    # ------------------------------------------------------------------
    # List management
    # ------------------------------------------------------------------

    """
    Creates a list in a space so each project workflow has a dedicated destination.
    """

    def create_space_list(
        self,
        space_id: str,
        name: str,
        content: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "name": name,
        }

        if content:
            payload["content"] = content

        return self.post(
            f"/space/{space_id}/list",
            json=payload,
        )

    """
    Updates list settings so an existing ClickUp list can match the project's workflow needs.
    """

    def update_list(
        self,
        list_id: str,
        name: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {}

        if name is not None:
            payload["name"] = name

        return self.put(
            f"/list/{list_id}",
            json=payload,
        )

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    """
    Creates a task so schedule, billing, or cash-flow records can be shared with the team.
    """

    def create_task(
        self,
        list_id: str,
        name: str,
        description: str | None = None,
        start_date: int | None = None,
        due_date: int | None = None,
        time_estimate: int | None = None,
        status: str | None = None,
        parent: str | None = None,
        notify_all: bool = False,
    ) -> Any:
        payload: dict[str, Any] = {
            "name": name,
            "notify_all": notify_all,
        }

        if description is not None:
            payload["description"] = description

        if start_date is not None:
            payload["start_date"] = start_date
            payload["start_date_time"] = False

        if due_date is not None:
            payload["due_date"] = due_date
            payload["due_date_time"] = False

        if time_estimate is not None:
            payload["time_estimate"] = time_estimate

        if status is not None:
            payload["status"] = status

        if parent is not None:
            payload["parent"] = parent

        return self.post(
            f"/list/{list_id}/task",
            json=payload,
        )

    """
    Updates a task so repeated imports can keep ClickUp aligned with current source data.
    """

    def update_task(
        self,
        task_id: str,
        name: str | None = None,
        description: str | None = None,
        start_date: int | None = None,
        due_date: int | None = None,
        time_estimate: int | None = None,
        status: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {}

        if name is not None:
            payload["name"] = name

        if description is not None:
            payload["description"] = description

        if start_date is not None:
            payload["start_date"] = start_date
            payload["start_date_time"] = False

        if due_date is not None:
            payload["due_date"] = due_date
            payload["due_date_time"] = False

        if time_estimate is not None:
            payload["time_estimate"] = time_estimate

        if status is not None:
            payload["status"] = status

        return self.put(
            f"/task/{task_id}",
            json=payload,
        )

    """
    Sets a task's parent so imported activities follow the source work-breakdown structure.
    """

    def update_task_parent(
        self,
        task_id: str,
        parent: str,
    ) -> Any:
        """Move an existing task under a ClickUp parent task."""

        return self.put(
            f"/task/{task_id}",
            json={"parent": parent},
        )

    """
    Fetches one task so callers can inspect its current values before making a change.
    """

    def get_task(self, task_id: str) -> Any:
        return self.get(f"/task/{task_id}")

    """
    Deletes one task through the shared session so the client exposes the API removal operation.
    """

    def delete_task(self, task_id: str) -> Any:
        """Delete a ClickUp task by ID."""

        return self.delete(
            f"/task/{task_id}",
        )
