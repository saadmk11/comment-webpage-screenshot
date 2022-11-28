import json
import os
import subprocess
import sys
import time
from functools import cached_property

import requests
from config import Configuration
from helpers import print_message
from image_upload_services import (
    GitHubBranchImageUploadService,
    ImgurImageUploadService,
)


class WebpageScreenshotAction:
    """
    Capture Screenshots from Webpage URL/HTML File Path
    and Comment it on Pull Request.
    """

    GITHUB_API_URL = "https://api.github.com"

    def __init__(self, configuration):
        self.configuration = configuration

    @cached_property
    def _request_headers(self):
        """Get headers for GitHub API request"""
        return {
            "Accept": "application/vnd.github.v3+json",
            "authorization": f"Bearer {self.configuration.GITHUB_TOKEN}",
        }

    @staticmethod
    def _capture_screenshot(filename, url_or_file_path):
        """Capture a screenshot from url or file path"""
        launch_options = {"args": ["--no-sandbox"]}
        screenshot_capture_command = [
            "capture-website",
            "--launch-options",
            f"{json.dumps(launch_options)}",
            "--full-page",
            url_or_file_path,
        ]

        try:
            return subprocess.check_output(screenshot_capture_command)
        except subprocess.CalledProcessError as e:
            msg = (
                f'Error while trying to Capture Screenshot for "{url_or_file_path}". '
                f"Error: {e.output}"
            )
            print_message(msg, message_type="error")
            return None

    def _get_pull_request_changed_files(self):
        """Gets changed files from the pull request"""
        pull_request_url = (
            f"{self.GITHUB_API_URL}/repos/{self.configuration.GITHUB_REPOSITORY}/pulls/"
            f"{self.configuration.GITHUB_PULL_REQUEST_NUMBER}/files"
        )
        response = requests.get(pull_request_url, headers=self._request_headers)
        if response.status_code != 200:
            # API should return 200, otherwise show error message
            msg = (
                "Error while trying to get pull request data. "
                "GitHub API returned error response for "
                f"{self.configuration.GITHUB_REPOSITORY}, "
                f"status code: {response.status_code}"
            )
            print_message(msg, message_type="error")
            return []

        # Return changed/added html files
        return [
            file["filename"]
            for file in response.json()
            if file["filename"].endswith(".html") and file["status"] != "removed"
        ]

    def _comment_screenshots(self, images):
        """Comments Screenshots to the pull request"""
        string_data = "## Here are the Screenshots after the Latest Changes\n\n"

        for image in images:
            file_path, filename, url = (
                image["file_path"],
                image["filename"],
                image["url"],
            )
            string_data += f"### {file_path}\n<kbd> ![{filename}]({url})\n"

        comment_url = (
            f"{self.GITHUB_API_URL}/repos/{self.configuration.GITHUB_REPOSITORY}/"
            f"issues/{self.configuration.GITHUB_PULL_REQUEST_NUMBER}/comments"
        )

        response = requests.post(
            comment_url, headers=self._request_headers, json={"body": string_data}
        )

        if response.status_code != 201:
            # API should return 201, otherwise show error message
            msg = (
                "Error while trying to create a comment. "
                "GitHub API returned error response for "
                f"{self.configuration.GITHUB_REPOSITORY}, "
                f"status code: {response.status_code}"
            )
            print_message(msg, message_type="error")

    def _get_image_upload_service(self):
        """Get image upload service"""
        if self.configuration.UPLOAD_TO == self.configuration.UPLOAD_SERVICE_IMGUR:
            return ImgurImageUploadService
        elif (
            self.configuration.UPLOAD_TO
            == self.configuration.UPLOAD_SERVICE_GITHUB_BRANCH
        ):
            return GitHubBranchImageUploadService
        else:
            return NotImplemented

    def _get_image_filename(self, file_path):
        """Generate Filename from url or file path"""
        return (
            (
                f"pr-{self.configuration.GITHUB_PULL_REQUEST_NUMBER}-{file_path}"
                f"-{int(time.time())}.png"
            )
            .replace("/", "-")
            .replace(" ", "")
        )

    def run(self):
        # Merge URLs and File Paths Together
        to_capture_list = (
            self.configuration.CAPTURE_URLS + self.configuration.CAPTURE_HTML_FILE_PATHS
        )

        if self.configuration.CAPTURE_CHANGED_HTML_FILES:
            # Add Pull request changed/added HTML files to `to_capture_list`
            changed_files = self._get_pull_request_changed_files()
            to_capture_list += changed_files

        # Get Image Upload Service Class and Initialize it
        image_upload_service = self._get_image_upload_service()(self.configuration)

        for item in set(to_capture_list):
            file_path = item
            # Generate Image Filename
            filename = self._get_image_filename(file_path)
            # Group: Webpage Screen Capture
            print_message(f'Capture Screenshot for "{file_path}"', message_type="group")
            # Capture Screenshot
            image_data = self._capture_screenshot(filename, item)
            print_message("", message_type="endgroup")
            # Add Image to Uploader Service
            if image_data:
                image_upload_service.add(file_path, filename, image_data)

        uploaded_images = image_upload_service.upload()

        # If any screenshot is uploaded comment the screenshots to the Pull Request
        if uploaded_images:
            print_message("Comment Webpage Screenshot", message_type="group")
            self._comment_screenshots(uploaded_images)
            print_message("", message_type="endgroup")


if __name__ == "__main__":
    print_message("Parse Configuration", message_type="group")
    environment = os.environ
    configuration = Configuration.from_environment(environment)
    print_message("", message_type="endgroup")

    # If the workflow was not triggered by a pull request
    # Exit the script with code 1.
    if configuration.GITHUB_EVENT_NAME not in configuration.SUPPORTED_EVENT_NAMES:
        print_message(
            "This action only works for "
            f'"{configuration.SUPPORTED_EVENT_NAMES}" event(s)',
            message_type="error",
        )
        sys.exit(1)

    # Initialize the Webpage Screenshot Action
    action = WebpageScreenshotAction(configuration)
    # Run Action
    action.run()
