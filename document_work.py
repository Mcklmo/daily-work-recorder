import os
import logging
import pendulum
from typing import Dict, List, Optional, Any
from notion_client import Client
import argparse
import json
import dotenv
import requests

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class NotionWorkRecorder:
    """A class to record work activities to a Notion database"""

    def __init__(self, notion_token: str, database_id: str, debug: bool = False):
        """
        Initialize the Notion Work Recorder

        Args:
            notion_token: Notion API token
            database_id: ID of the Notion database to write to
            debug: Enable debug logging
        """
        self.debug = debug
        self.notion = Client(auth=notion_token)
        self.database_id = database_id
        self.notion_token = notion_token

        # Validate the database connection
        self._validate_database()

    def debug_log(self, message: str, data: Any = None):
        """Print debug information if debug mode is enabled"""
        if self.debug:
            logger.info(f"[DEBUG] {message}")
            if data is not None:
                if isinstance(data, (dict, list)):
                    logger.info(
                        f"[DEBUG] Data: {json.dumps(data, indent=2, default=str)}"
                    )
                else:
                    logger.info(f"[DEBUG] Data: {data}")

    def _validate_database(self):
        """Validate that we can access the database"""
        database = self.notion.databases.retrieve(database_id=self.database_id)
        self.debug_log("Database validation successful", database.get("title"))
        return database

    def get_database_schema(self) -> Dict[str, Any]:
        """Get the schema of the database"""
        response = requests.get(
            f"https://api.notion.com/v1/databases/{self.database_id}",
            headers={
                "Authorization": f"Bearer {self.notion_token}",
                "Notion-Version": "2022-06-28",
            },
        )
        response.raise_for_status()
        return response.json()

    def find_page_by_title(self, database_id: str, title: str) -> Optional[str]:
        """
        Find a page in a database by its title

        Args:
            database_id: The ID of the database to search in
            title: The title to search for

        Returns:
            The page ID if found, None otherwise
        """
        response = requests.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers={
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            },
            json={
                "filter": {
                    "property": "title",
                    "rich_text": {"equals": "Time registration codes"},
                }
            },
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                return data["results"][0]["id"]

        return None

    def get_project_code_database_id(self) -> Optional[str]:
        """
        Get the database ID that the Project code relation property references

        Returns:
            The database ID if found, None otherwise
        """
        schema = self.get_database_schema()
        project_code_prop = schema.get("properties", {}).get("Project code")

        if project_code_prop and project_code_prop.get("type") == "relation":
            return project_code_prop.get("relation", {}).get("database_id")

        return None

    def create_work_record(
        self,
        title: str,
        description: str = "",
        date: Optional[pendulum.DateTime] = None,
        tags: Optional[List[str]] = None,
        duration: Optional[int] = None,
        project: Optional[str] = None,
        **additional_properties,
    ) -> Dict[str, Any]:
        """
        Create a work record in Notion

        Args:
            title: Title of the work record
            description: Description of the work
            date: Date of the work (defaults to today)
            tags: List of tags for the work
            duration: Duration in minutes
            project: Project name
            **additional_properties: Additional properties to set

        Returns:
            The created page object from Notion
        """

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            },
            json={
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Created by": {
                        "people": [
                            {
                                "object": "user",
                                "id": "9b0092bf-47c7-465c-b5ac-5760d0450d07",
                            }
                        ]
                    },
                    "Date": {
                        "date": {
                            "start": date.to_date_string(),
                        }
                    },
                    "Hours": {
                        "number": 0,
                    },
                    "Project code": {
                        "relation": [
                            {
                                "id": "12320972-3be0-80cd-84da-e2550442ac9f",
                            }
                        ]
                    },
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": description or ""},
                                }
                            ]
                        },
                    }
                ],
            },
        )

        data = response.json()
        if data.get("object") == "error":
            raise Exception(data.get("message"))

        response.raise_for_status()
        return data

    def create_daily_summary(
        self,
        date: pendulum.DateTime,
        commits: List[Dict[str, Any]],
        total_commits: int,
        repositories: List[str],
    ) -> Dict[str, Any]:
        """
        Create a daily summary record based on git activity

        Args:
            date: Date of the activity
            commits: List of commit information
            total_commits: Total number of commits
            repositories: List of repository names

        Returns:
            The created page object from Notion
        """
        # Create a summary of the day's work
        title = f"Development Work - {date.format('YYYY-MM-DD')}"

        # Create description from commits
        description_parts = [
            f"Total commits: {total_commits}",
            f"Repositories: {', '.join(repositories)}",
            "",
            "Commit Summary:",
        ]

        for commit in commits[:10]:  # Show first 10 commits
            description_parts.append(f"• {commit.get('message', 'No message')}")

        if len(commits) > 10:
            description_parts.append(f"• ... and {len(commits) - 10} more commits")

        description = "\n".join(description_parts)

        # Create tags based on repositories
        tags = repositories[:5]  # Limit to 5 tags

        return self.create_work_record(
            title=title,
            description=description,
            date=date,
            tags=tags,
            project="Development",
            duration=None,  # Could be calculated based on commit frequency
        )

    def bulk_create_records(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple work records

        Args:
            records: List of record dictionaries with keys matching create_work_record parameters

        Returns:
            List of created page objects
        """
        created_pages = []

        for record in records:
            page = self.create_work_record(**record)
            created_pages.append(page)

        logger.info(f"Created {len(created_pages)} out of {len(records)} records")
        return created_pages


def main():
    """Main function to demonstrate usage"""
    parser = argparse.ArgumentParser(description="Record work activities to Notion")
    parser.add_argument(
        "--notion-token",
        type=str,
        help="Notion API token (or set NOTION_API_KEY environment variable)",
        default=os.getenv("NOTION_API_KEY"),
    )
    parser.add_argument(
        "--database-id",
        type=str,
        help="Notion database ID (or set NOTION_DATABASE_ID environment variable)",
        default=os.getenv("NOTION_DATABASE_ID"),
    )
    parser.add_argument(
        "--title",
        type=str,
        help="Title of the work record",
        default="Sample Work Record",
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Description of the work done",
        default="This is a sample work record created by the document_work.py script",
    )
    parser.add_argument(
        "--project", type=str, help="Project name", default="Daily Work Recorder"
    )
    parser.add_argument(
        "--tags",
        type=str,
        help="Comma-separated list of tags",
        default="development,python,automation",
    )
    parser.add_argument("--duration", type=int, help="Duration in minutes", default=30)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
        default=True,
    )
    parser.add_argument(
        "--show-schema", action="store_true", help="Show the database schema and exit"
    )

    args = parser.parse_args()

    # Validate required arguments
    if not args.notion_token:
        logger.error(
            "Notion token is required. Set NOTION_TOKEN environment variable or use --notion-token"
        )
        return 1

    if not args.database_id:
        logger.error(
            "Database ID is required. Set NOTION_DATABASE_ID environment variable or use --database-id"
        )
        return 1

    # Initialize the recorder
    recorder = NotionWorkRecorder(
        notion_token=args.notion_token,
        database_id=args.database_id,
        debug=args.debug,
    )

    # Show schema if requested
    if args.show_schema:
        schema = recorder.get_database_schema()
        print("Database Schema:")
        for prop_name, prop_details in schema.items():
            print(f"  {prop_name}: {prop_details['type']}")
        return 0

    # Create a sample work record
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]

    result = recorder.create_work_record(
        title=args.title,
        description=args.description,
        date=pendulum.now(),
        tags=tags,
        duration=args.duration,
        project=args.project,
    )

    print(f"Successfully created work record: {result['id']}")
    print(f"URL: {result['url']}")

    return 0


if __name__ == "__main__":
    exit(main())
