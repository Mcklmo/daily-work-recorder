import os
from calculate_work_hours.calc import report_daily_work
from write_to_mock import MockWorkRecorder
from write_to_notion import NotionWorkRecorder
from read_git_cli import GitActivityTracker
from logger import logger
import dotenv
from get_user_input.from_cli import UserInputCLI


dotenv.load_dotenv()


def must_get_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise Exception(f"Environment variable {key} is not set")

    return value


def main() -> None:
    notion_database_id = must_get_env("NOTION_DATABASE_ID")
    notion_token = must_get_env("NOTION_API_KEY")
    work_recorder = NotionWorkRecorder(
        notion_token=notion_token, database_id=notion_database_id
    )
    activity_tracker = GitActivityTracker()
    report_daily_work(
        UserInputCLI(),
        MockWorkRecorder(logger),
        activity_tracker,
        logger,
    )


if __name__ == "__main__":
    main()
