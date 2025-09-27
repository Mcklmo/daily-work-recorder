import pendulum
from calculate_work_hours.calc import UserInputGetter, UserInput
import argparse


class UserInputCLI(UserInputGetter):
    def get_user_input(self) -> UserInput:
        parser = argparse.ArgumentParser(
            description="BCT Git activity tracker for Notion"
        )
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
            type=int,
            help="Work duration in hours (default: 0)",
            default=0,
        )
        parser.add_argument(
            "-d",
            "--date",
            type=str,
            help="Date of the work (YYYY-MM-DD) (default: empty)",
            default=None,
        )
        parser.add_argument(
            "-s",
            "--start-date",
            type=str,
            help="Start date of the work (YYYY-MM-DD) (default: empty)",
            default=None,
        )
        parser.add_argument(
            "-e",
            "--end-date",
            type=str,
            help="End date of the work (YYYY-MM-DD) (default: empty)",
            default=None,
        )

        args = parser.parse_args()
        date_format = "YYYY-MM-DD"

        return UserInput(
            date=pendulum.from_format(args.date, date_format) if args.date else None,
            work_repository_path=args.work_repository_path,
            git_username=args.git_username,
            notion_project=args.notion_project,
            notion_user_name=args.notion_user_name,
            duration_hours=args.duration_hours,
            start_date=(
                pendulum.from_format(args.start_date, date_format)
                if args.start_date
                else None
            ),
            end_date=(
                pendulum.from_format(args.end_date, date_format)
                if args.end_date
                else None
            ),
        )
