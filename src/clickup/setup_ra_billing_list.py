"""Create the Kaveri RA Billing ClickUp List idempotently."""

from dotenv import load_dotenv

from src.clickup.client import ClickUpClient


SPACE_ID = "1300410000030282"
TARGET_LIST_NAME = "RA Billing"


def main() -> None:
    load_dotenv()

    client = ClickUpClient()

    lists_result = client.get_space_lists(SPACE_ID)
    lists = lists_result.get("lists", [])

    existing = next(
        (
            item
            for item in lists
            if item.get("name") == TARGET_LIST_NAME
        ),
        None,
    )

    if existing:
        print("RA Billing List already exists.")
        print(f"Name: {existing.get('name')}")
        print(f"ID: {existing.get('id')}")
        return

    created = client.create_space_list(
        SPACE_ID,
        TARGET_LIST_NAME,
        content=(
            "Kaveri Infrasystems SCP2 — RA billing records. "
            "Commercial values and client data remain inside "
            "the company-controlled ClickUp workspace."
        ),
    )

    print("RA Billing List created successfully.")
    print(f"Name: {created.get('name')}")
    print(f"ID: {created.get('id')}")


if __name__ == "__main__":
    main()