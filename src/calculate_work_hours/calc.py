from abc import abstractmethod
from logging import Logger

import pendulum


class UserInput:
    def __init__(
        self,
        date: pendulum.DateTime | None,
        work_repository_path: str,
        git_username: str,
        notion_project: str,
        notion_user_name: str,
        duration_hours: int,
        start_date: pendulum.DateTime | None,
        end_date: pendulum.DateTime | None,
    ):
        if date and (start_date or end_date):
            raise Exception("Date and start/end date cannot be used together")

        if date:
            start_date = date
            end_date = date

        if not start_date:
            start_date = pendulum.now()

        if not end_date:
            end_date = pendulum.now()

        self.date = date
        self.work_repository_path = work_repository_path
        self.git_username = git_username
        self.notion_project = notion_project
        self.notion_user_name = notion_user_name
        self.duration_hours = duration_hours
        self.start_date: pendulum.DateTime = start_date
        self.end_date: pendulum.DateTime = end_date


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
    def get_daily_work(
        self,
        username: str,
        work_repository_path: str,
        target_date_range: pendulum.Interval,
    ) -> dict[str, str]:
        pass


def report_daily_work(
    user_input_getter: UserInputGetter,
    work_recorder: WorkRecorder,
    activity_tracker: ActivityTracker,
    logger: Logger,
) -> None:
    args = user_input_getter.get_user_input()
    report = activity_tracker.get_daily_work(
        args.git_username,
        args.work_repository_path,
        pendulum.interval(  # get more than needed from git history just to be sure
            args.start_date.subtract(days=1),
            args.end_date.add(days=1),
        ),
    )

    for target_date in pendulum.interval(args.start_date, args.end_date).range("days"):
        target_date_str = target_date.to_date_string()
        if target_date_str not in report:
            logger.error(f"No work found for date {target_date_str}")
            continue

        work_recorder.create_work_record(
            description=report[target_date_str],
            date=target_date,
            duration=args.duration_hours,
            project=args.notion_project,
            user_name=args.notion_user_name,
        )
