import dataclasses
from typing import List


@dataclasses.dataclass
class Configuration:
    """Configuration for Webpage Image Capture Action"""
    # Default environment variable from GitHub
    # https://docs.github.com/en/actions/configuring-and-managing-workflows/using-environment-variables
    GITHUB_REF: str
    GITHUB_REPOSITORY: str
    GITHUB_TOKEN: str
    GITHUB_EVENT_NAME: str

    UPLOAD_SERVICE_GITHUB_BRANCH: str = 'github_branch'
    UPLOAD_SERVICE_IMGUR: str = 'imgur'

    PULL_REQUEST_EVENT: str = 'pull_request'
    SUPPORTED_EVENT_NAMES: list = dataclasses.field(
        default_factory=lambda: ['pull_request']
    )

    UPLOAD_TO: str = UPLOAD_SERVICE_GITHUB_BRANCH
    CAPTURE_HTML_FILE_PATHS: List[str] = dataclasses.field(default_factory=list)
    CAPTURE_URLS: List[str] = dataclasses.field(default_factory=list)
    CAPTURE_CHANGED_HTML_FILES: bool = True

    @staticmethod
    def convert_string_to_list(string):
        """Helper method to convert a comma seperated string to a list"""
        if not isinstance(string, str):
            return []
        return [s.lstrip().rstrip() for s in string.strip().split(',') if s]

    @classmethod
    def validate_input_capture_html_file_paths(cls, value):
        return cls.convert_string_to_list(value)

    @classmethod
    def validate_input_capture_urls(cls, value):
        return cls.convert_string_to_list(value)

    @classmethod
    def validate_input_capture_changed_html_files(cls, value):
        return str(value).lower() in ("1", "true", "yes")

    @classmethod
    def validate_input_upload_to(cls, value):
        if str(value).lower() not in [
            cls.UPLOAD_SERVICE_GITHUB_BRANCH,
            cls.UPLOAD_SERVICE_IMGUR
        ]:
            return cls.UPLOAD_SERVICE_GITHUB_BRANCH
        return value

    @classmethod
    def from_environment(cls, environment):
        available_environment_variables = [
            'GITHUB_REPOSITORY',
            'GITHUB_REF',
            'GITHUB_TOKEN',
            'GITHUB_EVENT_NAME',
            'INPUT_UPLOAD_TO',
            'INPUT_CAPTURE_CHANGED_HTML_FILES',
            'INPUT_CAPTURE_HTML_FILE_PATHS',
            'INPUT_CAPTURE_URLS'
        ]

        config = {}

        for key, value in environment.items():
            if key in available_environment_variables and value not in [None, '', []]:
                func = getattr(cls, f'validate_{key.lower()}', None)
                config_key = (
                    key.replace('INPUT_', '', 1)
                    if key.startswith('INPUT_') else key
                )
                if func:
                    config[config_key] = func(value)
                else:
                    config[config_key] = value

        return cls(**config)

    @property
    def GITHUB_PULL_REQUEST_NUMBER(self):
        if "refs/pull/" in self.GITHUB_REF:
            return int(self.GITHUB_REF.split("/")[2])
        return None
