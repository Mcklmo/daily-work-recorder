import argparse
import os
import pendulum
from write_to_notion import NotionWorkRecorder
from read_git_cli import GitActivityTracker
from logger import logger
import dotenv


dotenv.load_dotenv()


def parse_args() -> tuple[str, str, str, str, str, float]:
    parser = argparse.ArgumentParser(description="BCT Git activity tracker for Notion")
    parser.add_argument(
        "-r",
        "--work-repository-path",
        type=str,
        help="Path to the work repository. This will be scanned for git repositories.",
        required=True,
    )
    parser.add_argument(
        "-g",
        "--git-username",
        type=str,
        help="git username to filter by. This will be used to filter the git repositories.",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--notion-project",
        type=str,
        help="Notion project name. This will be used to find the project in our Time Registration Codes database and add it to the work record.",
        required=True,
    )
    parser.add_argument(
        "-n",
        "--notion-user-name",
        type=str,
        help="Notion user name. This will be used to find your user in the Notion database and add it to the work record.",
        required=True,
    )
    parser.add_argument(
        "-dh",
        "--duration-hours",
        type=float,
        help="Work duration in hours (default: 0)",
        default=0,
    )
    parser.add_argument(
        "-d",
        "--date",
        type=str,
        help="Date of the work (YYYY-MM-DD) (default: today)",
        default=pendulum.now().to_date_string(),
    )

    args = parser.parse_args()

    return (
        args.date,
        args.work_repository_path,
        args.git_username,
        args.notion_project,
        args.notion_user_name,
        args.duration_hours,
    )


def must_get_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise Exception(f"Environment variable {key} is not set")

    return value


def main():
    notion_token = must_get_env("NOTION_API_KEY")
    notion_database_id = must_get_env("NOTION_DATABASE_ID")
    (
        arg_date,
        args_work_repository_path,
        args_git_username,
        args_notion_project,
        args_notion_user_name,
        args_duration_hours,
    ) = parse_args()

    target_date = pendulum.parse(arg_date)
    tracker = GitActivityTracker(debug=False)

    git_repos = tracker.find_git_repos_in_directory(args_work_repository_path, 3)
    if not git_repos:
        raise Exception(
            f"No git repositories found in path {args_work_repository_path}"
        )

    report = tracker.get_multiple_repos_daily_work(
        git_repos,
        args_git_username,
        pendulum.interval(  # get more than needed from git history just to be sure
            target_date.subtract(days=1),
            target_date.add(days=1),
        ),
    )

    target_date_str = target_date.to_date_string()
    if target_date_str not in report:
        logger.error(f"No work found for date {target_date_str}")
        return

    result = NotionWorkRecorder(
        notion_token=notion_token,
        database_id=notion_database_id,
    ).create_work_record(
        description=report[target_date_str],
        date=target_date,
        duration=args_duration_hours,
        project=args_notion_project,
        user_name=args_notion_user_name,
    )

    logger.info(f"Successfully created work record: {result['url']}")


if __name__ == "__main__":
    main()
