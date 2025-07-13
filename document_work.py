import pendulum
from typing import Dict, List, Optional, Any
from notion_client import Client
import dotenv
import requests
from logger import logger

dotenv.load_dotenv()


class NotionWorkRecorder:
    def __init__(self, notion_token: str, database_id: str, debug: bool = False):
        self.debug = debug
        self.notion = Client(auth=notion_token)
        self.database_id = database_id
        self.notion_token = notion_token

        self._validate_database()

    def _validate_database(self):
        self.notion.databases.retrieve(database_id=self.database_id)

    def get_database_schema(self) -> Dict[str, Any]:
        response = requests.get(
            f"https://api.notion.com/v1/databases/{self.database_id}",
            headers={
                "Authorization": f"Bearer {self.notion_token}",
                "Notion-Version": "2022-06-28",
            },
        )
        response.raise_for_status()
        return response.json()

    def get_project_code_id(self, project_name: str) -> Optional[str]:
        schema = self.get_database_schema()
        project_code_prop = schema.get("properties", {}).get("Project code")
        time_registration_codes_db_id = project_code_prop.get("relation", {}).get(
            "database_id"
        )

        all_projects = self.notion.databases.query(
            database_id=time_registration_codes_db_id,
            filter={"property": "title", "rich_text": {"equals": project_name}},
        )

        return all_projects["results"][0]["id"]

    def get_user_id(self, user_name: str) -> str:
        all_users = self.notion.users.list()

        for user in all_users["results"]:
            if user["name"] == user_name:
                return user["id"]

        raise Exception(f"User {user_name} not found")

    def create_work_record(
        self,
        description: str,
        date: pendulum.DateTime,
        duration: int,
        project: str,
        user_name: str,
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
                                "id": self.get_user_id(user_name),
                            }
                        ]
                    },
                    "Date": {
                        "date": {
                            "start": date.to_date_string(),
                        }
                    },
                    "Hours": {
                        "number": duration,
                    },
                    "Project code": {
                        "relation": [
                            {
                                "id": self.get_project_code_id(project),
                            }
                        ]
                    },
                },
                "children": [
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": description},
                                }
                            ],
                            "language": "markdown",
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
