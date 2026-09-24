"""Create the first Kaveri ClickUp List idempotently."""

import os

from dotenv import load_dotenv

from src.clickup.client import ClickUpClient


SPACE_ID = "1300410000030282"
EXISTING_LIST_ID = "1300410000039999"
TARGET_LIST_NAME = "Schedule & WBS"


def main() -> None:
    load_dotenv()

    client = ClickUpClient()

    existing = client.get_list(EXISTING_LIST_ID)

    print("Current List:")
    print(f"  Name: {existing.get('name')}")
    print(f"  ID: {existing.get('id')}")

    tasks_result = client.get_list_tasks(EXISTING_LIST_ID)
    tasks = tasks_result.get("tasks", [])

    if tasks:
        raise RuntimeError(
            "Refusing to rename the existing List because it contains tasks."
        )

    current_name = existing.get("name")

    if current_name == TARGET_LIST_NAME:
        print()
        print("Schedule & WBS List already exists.")
        print(f"List ID: {EXISTING_LIST_ID}")
        return

    client.update_list(
        EXISTING_LIST_ID,
        name=TARGET_LIST_NAME,
    )

    updated = client.get_list(EXISTING_LIST_ID)

    print()
    print("Schedule & WBS List configured successfully.")
    print(f"Name: {updated.get('name')}")
    print(f"ID: {updated.get('id')}")


if __name__ == "__main__":
    main()