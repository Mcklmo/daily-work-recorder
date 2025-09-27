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
            default="",
        )
        parser.add_argument(
            "-s",
            "--start-date",
            type=str,
            help="Start date of the work (YYYY-MM-DD) (default: empty)",
            default="",
        )
        parser.add_argument(
            "-e",
            "--end-date",
            type=str,
            help="End date of the work (YYYY-MM-DD) (default: empty)",
            default="",
        )

        args = parser.parse_args()

        return UserInput(
            date=args.date,
            work_repository_path=args.work_repository_path,
            git_username=args.git_username,
            notion_project=args.notion_project,
            notion_user_name=args.notion_user_name,
            duration_hours=args.duration_hours,
            start_date=args.start_date,
            end_date=args.end_date,
        )
