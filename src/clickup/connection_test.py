"""Read-only ClickUp workspace structure discovery."""

import os

from dotenv import load_dotenv

from src.clickup.client import ClickUpClient


def main() -> None:
    load_dotenv()

    workspace_id = os.getenv("CLICKUP_WORKSPACE_ID")

    if not workspace_id:
        raise ValueError("CLICKUP_WORKSPACE_ID is not configured")

    client = ClickUpClient()

    spaces_result = client.get_spaces(workspace_id)
    spaces = spaces_result.get("spaces", [])

    print("Kaveri ClickUp workspace discovery successful.")
    print()
    print(f"Workspace ID: {workspace_id}")
    print(f"Spaces found: {len(spaces)}")
    print()

    for space in spaces:
        space_id = space.get("id")
        space_name = space.get("name")

        print(f"Space: {space_name}")
        print(f"ID: {space_id}")

        folders_result = client.get_folders(space_id)
        folders = folders_result.get("folders", [])

        print(f"Folders found: {len(folders)}")

        for folder in folders:
            print(
                f"  - {folder.get('name')} "
                f"(ID: {folder.get('id')})"
            )

        lists_result = client.get_space_lists(space_id)
        lists = lists_result.get("lists", [])

        print(f"Lists found directly in Space: {len(lists)}")

        for item in lists:
            list_id = item.get("id")

            print(
                f"  - {item.get('name')} "
                f"(ID: {list_id})"
            )

            details = client.get_list(list_id)

            print(
                f"    Status: {details.get('status', {}).get('status')}"
            )

            tasks_result = client.get_list_tasks(list_id)
            tasks = tasks_result.get("tasks", [])

            print(f"    Tasks found: {len(tasks)}")

            custom_fields = details.get("fields", [])
            print(f"    Custom fields: {len(custom_fields)}")

            for field in custom_fields:
                print(
                    f"      - {field.get('name')} "
                    f"(ID: {field.get('id')})"
                )

        print()


if __name__ == "__main__":
    main()