import pendulum
from logging import Logger
from calculate_work_hours.calc import WorkRecorder


class MockWorkRecorder(WorkRecorder):
    def __init__(self, logger: Logger):
        self.logger = logger

    def create_work_record(
        self,
        description: str,
        date: pendulum.DateTime,
        duration: int,
        project: str,
        user_name: str,
    ) -> None:
        self.logger.info(
            f"Creating work record",
            {
                "description": description,
                "date": date,
                "duration": duration,
                "project": project,
                "user_name": user_name,
            },
        )
