import dataclasses
from typing import List


@dataclasses.dataclass
class Configuration:
    """Configuration for Comment Webpage Screenshot Action"""

    # Default environment variable from GitHub
    # https://docs.github.com/en/actions/configuring-and-managing-workflows/using-environment-variables
    GITHUB_REF: str
    GITHUB_REPOSITORY: str
    GITHUB_TOKEN: str
    GITHUB_EVENT_NAME: str
    GITHUB_RUN_ID: str
    GITHUB_SHA: str

    UPLOAD_SERVICE_GITHUB_BRANCH: str = "github_branch"
    UPLOAD_SERVICE_IMGUR: str = "imgur"

    PULL_REQUEST_EVENT: str = "pull_request"
    SUPPORTED_EVENT_NAMES: list = dataclasses.field(
        default_factory=lambda: ["pull_request"]
    )

    UPLOAD_TO: str = UPLOAD_SERVICE_GITHUB_BRANCH
    IMAGES: List[str] = dataclasses.field(default_factory=list)
    CUSTOM_ATTACHMENT_MSG: str = "Screenshots for commit"
    EDIT_PREVIOUS_COMMENT: bool = True

    @staticmethod
    def convert_string_to_list(string):
        """Helper method to convert a comma seperated string to a list"""
        if not isinstance(string, str):
            return []
        return [s.lstrip().rstrip() for s in string.strip().split(",") if s]

    @classmethod
    def validate_images(cls, value):
        return cls.convert_string_to_list(value)

    @classmethod
    def validate_upload_to(cls, value):
        value = str(value).lower()
        if value not in [cls.UPLOAD_SERVICE_GITHUB_BRANCH, cls.UPLOAD_SERVICE_IMGUR]:
            return cls.UPLOAD_SERVICE_GITHUB_BRANCH
        return value

    @classmethod
    def validate_custom_attachment_msg(cls, value):
        if not value:
            raise ValueError("CUSTOM_ATTACHMENT_MSG cannot be an empty string!")

    @classmethod
    def validate_edit_previous_comment(cls, value):
        if not isinstance(value, bool):
            return value.lower() == "true"

    @classmethod
    def from_environment(cls, environment):
        """Initialize Configuration from Environment Variables"""
        available_environment_variables = [
            "GITHUB_REPOSITORY",
            "GITHUB_REF",
            "GITHUB_EVENT_NAME",
            "GITHUB_RUN_ID",
            "GITHUB_SHA",
            "INPUT_GITHUB_TOKEN",
            "INPUT_IMAGES",
            "INPUT_CUSTOM_ATTACHMENT_MSG",
            "INPUT_EDIT_PREVIOUS_COMMENT",
            "INPUT_UPLOAD_TO",
            "INPUT_IMAGES",
        ]

        config = {}

        for key, value in environment.items():
            if key in available_environment_variables and value not in [None, "", []]:
                config_key = (
                    key.replace("INPUT_", "", 1) if key.startswith("INPUT_") else key
                )
                # Get Validate method for the config key
                func = getattr(cls, f"validate_{config_key.lower()}", None)

                if func:
                    config[config_key] = func(value)
                else:
                    config[config_key] = value

        return cls(**config)

    @property
    def GITHUB_PULL_REQUEST_NUMBER(self):
        """Get Pull Request Number from `GITHUB_REF`"""
        if "refs/pull/" in self.GITHUB_REF:
            return int(self.GITHUB_REF.split("/")[2])
        return None
