"""Importing this package registers every ORM model on Base.metadata."""

from app.models.api_key import ApiKey
from app.models.hint_usage import HintUsage
from app.models.instance_config import InstanceConfig
from app.models.lab_session import LabSession
from app.models.progress import Progress
from app.models.submission import Submission
from app.models.task import Task
from app.models.user import User

__all__ = [
    "ApiKey",
    "HintUsage",
    "InstanceConfig",
    "LabSession",
    "Progress",
    "Submission",
    "Task",
    "User",
]
