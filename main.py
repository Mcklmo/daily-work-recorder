import argparse
import os
import pendulum

from document_work import NotionWorkRecorder
from logger import logger
from record_git_cli import GitActivityTracker


def main():
    parser = argparse.ArgumentParser(
        description="Generate Git activity reports for Notion"
    )
    parser.add_argument(
        "--repo-path",
        "-r",
        type=str,
        help="Path to the git repository (default: current directory)",
        default="/Users/moritzmarcushonscheidt/Projects/work/bct/",
    )
    parser.add_argument(
        "--username",
        "-u",
        type=str,
        help="Git username to filter by",
        default="mcklmo",
    )
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
        default="ccfdf76c30084572b6699f2aada638cc",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        help="Work duration in hours",
        default=0,
    )
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        help="Description of the work",
        default="I did some work",
    )
    parser.add_argument(
        "--project",
        "-p",
        type=str,
        help="Project name",
        default="Danske Commodities",
    )
    parser.add_argument(
        "--user-name",
        "-U",
        type=str,
        help="Notion user name",
        default="Moritz Marcus Hönscheidt",
    )
    parser.add_argument(
        "--date",
        "-D",
        type=str,
        help="Date of the work (YYYY-MM-DD)",
        default=pendulum.now().to_date_string(),
    )

    args = parser.parse_args()
    if not args.notion_token:
        logger.error(
            "Notion token is required. Set NOTION_TOKEN environment variable or use --notion-token <token>"
        )
        return 1

    target_date = pendulum.parse(args.date)

    GITHUB_USERNAME = args.username
    REPO_PATH = args.repo_path

    period = pendulum.interval(target_date.subtract(days=1), target_date.add(days=1))
    temp_tracker = GitActivityTracker(debug=False)
    root_path = REPO_PATH or os.getcwd()

    git_repos = temp_tracker.find_git_repos_in_directory(root_path, 2)
    if not git_repos:
        raise Exception(f"No git repositories found in path {root_path}")

    report = temp_tracker.get_multiple_repos_daily_work(
        git_repos,
        GITHUB_USERNAME,
        period,
    )

    result = NotionWorkRecorder(
        notion_token=args.notion_token,
        database_id=args.database_id,
    ).create_work_record(
        description=report[target_date.to_date_string()],
        date=target_date,
        duration=args.duration,
        project=args.project,
        user_name=args.user_name,
    )

    print(f"Successfully created work record: {result['id']}")
    print(f"URL: {result['url']}")

    return 0


if __name__ == "__main__":
    main()
