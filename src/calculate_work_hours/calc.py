from abc import abstractmethod
from logging import Logger

import pendulum


class UserInput:
    def __init__(
        self,
        date: str,
        work_repository_path: str,
        git_username: str,
        notion_project: str,
        notion_user_name: str,
        duration_hours: int,
        start_date: str,
        end_date: str,
    ):
        if date and (start_date or end_date):
            raise Exception("Date and start/end date cannot be used together")

        if not date and not (start_date and end_date):
            date = pendulum.now().to_date_string()

        if start_date and not end_date or not start_date and end_date:
            start_date = date
            end_date = date

        self.date = date
        self.work_repository_path = work_repository_path
        self.git_username = git_username
        self.notion_project = notion_project
        self.notion_user_name = notion_user_name
        self.duration_hours = duration_hours
        self.start_date = start_date
        self.end_date = end_date


class UserInputGetter:
    @abstractmethod
    def get_user_input(self) -> UserInput:
        pass


class WorkRecorder:
    @abstractmethod
    def create_work_record(
        self,
        description: str,
        date: pendulum.DateTime,
        duration: int,
        project: str,
        user_name: str,
    ) -> None:
        pass


class ActivityTracker:
    @abstractmethod
    def get_multiple_repos_daily_work(
        self,
        username: str,
        work_repository_path: str,
        target_date_range: pendulum.Interval,
    ) -> dict[str, str]:
        pass


def calculate_work_hours(
    user_input_getter: UserInputGetter,
    work_recorder: WorkRecorder,
    activity_tracker: ActivityTracker,
    logger: Logger,
) -> None:
    args = user_input_getter.get_user_input()
    target_date = pendulum.parse(args.date)
    report = activity_tracker.get_multiple_repos_daily_work(
        args.git_username,
        args.work_repository_path,
        pendulum.interval(  # get more than needed from git history just to be sure
            target_date.subtract(days=1),
            target_date.add(days=1),
        ),
    )

    target_date_str = target_date.to_date_string()
    if target_date_str not in report:
        logger.error(f"No work found for date {target_date_str}")
        return

    work_recorder.create_work_record(
        description=report[target_date_str],
        date=target_date,
        duration=args.duration_hours,
        project=args.notion_project,
        user_name=args.notion_user_name,
    )
