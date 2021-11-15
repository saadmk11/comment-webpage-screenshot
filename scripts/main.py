import json
import os
import subprocess
import sys
import time
from functools import cached_property

import requests

import image_upload_services
from helpers import print_message, convert_string_to_list


class WebsiteScreenshot:
    """
    Capture Screenshots from Website URL/HTML File Path
    and Comment it on Pull Request.
    """

    GITHUB_API_URL = 'https://api.github.com'

    def __init__(
        self,
        token,
        repository,
        upload_to,
        event_path,
        capture_changed_html_files,
        capture_html_file_paths=None,
        capture_urls=None
    ):
        self.token = token
        self.repository = repository
        self.capture_changed_html_files = capture_changed_html_files
        self.upload_to = upload_to.lower()
        self.pull_request_number = self._get_pull_request_number(event_path)
        self.capture_html_file_paths = (
            convert_string_to_list(capture_html_file_paths)
            if capture_html_file_paths else []
        )
        self.capture_urls = (
            convert_string_to_list(capture_urls)
            if capture_urls else []
        )

    @staticmethod
    def _get_pull_request_number(event_path):
        """Gets pull request number from `GITHUB_EVENT_PATH`"""
        with open(event_path, 'r') as json_file:
            # This is just a webhook payload available to the Action
            data = json.load(json_file)
            number = data['number']

        return number

    @cached_property
    def _request_headers(self):
        """Get headers for GitHub API request"""
        return {
            'Accept': 'application/vnd.github.v3+json',
            'authorization': f'Bearer {self.token}'
        }

    def _capture_screenshot(self, filename, url_or_file_path):
        """Capture a screenshot from url or file path"""
        launch_options = {"args": ["--no-sandbox"]}
        screenshot_capture_command = [
            "capture-website",
            "--launch-options",
            f"{json.dumps(launch_options)}",
            "--full-page",
            url_or_file_path
        ]

        if self.upload_to == 'github_branch':
            directory = 'website-screenshots'
            os.makedirs(directory, exist_ok=True)
            screenshot_capture_command.append(f"--output={directory}/{filename}")

        return subprocess.check_output(screenshot_capture_command)

    def _get_pull_request_changed_files(self):
        """Gets changed files from the pull request"""
        pull_request_url = (
            f'{self.GITHUB_API_URL}/repos/{self.repository}/pulls/'
            f'{self.pull_request_number}/files'
        )
        response = requests.get(
            pull_request_url,
            headers=self._request_headers
        )
        if response.status_code != 200:
            # API should return 200, otherwise show error message
            msg = (
                f'Error while trying to get pull request data. '
                f'GitHub API returned error response for '
                f'{self.repository}, status code: {response.status_code}'
            )
            print_message(msg, message_type='error')
            return []

        # Return changed/added html files
        return [
            file['filename']
            for file in response.json()
            if file['filename'].endswith('.html')
            and file['status'] != 'removed'
        ]

    def _comment_screenshots(self, images):
        """Comments Screenshots to the pull request"""
        string_data = '## Here are the Screenshots after the Latest Changes\n\n'

        for image in images:
            display_name, filename, url = (
                image['display_name'], image['filename'], image['url']
            )
            string_data += f'### {display_name}\n![{filename}]({url})\n'

        comment_url = (
            f'{self.GITHUB_API_URL}/repos/{self.repository}/'
            f'issues/{self.pull_request_number}/comments'
        )

        response = requests.post(
            comment_url,
            headers=self._request_headers,
            json={
                'body': string_data
            }
        )

        if response.status_code != 201:
            # API should return 201, otherwise show error message
            msg = (
                f'Error while trying to create a comment. '
                f'GitHub API returned error response for '
                f'{self.repository}, status code: {response.status_code}'
            )
            print_message(msg, message_type='error')

    def _get_image_upload_service(self):
        """Get image upload service"""
        if self.upload_to == 'imgur':
            return image_upload_services.ImgurImageUploadService
        elif self.upload_to == 'github_branch':
            return image_upload_services.GitHubBranchImageUploadService
        else:
            return NotImplemented

    def _get_image_filename(self, display_name):
        """Generate Filename from url or file path"""
        return (
            f'pr-{self.pull_request_number}-{display_name}'
            f'-{int(time.time())}.png'
        ).replace('/', '-').replace(' ', '')

    def run(self):
        # Merge URLs and File Paths Together
        to_capture_list = self.capture_urls + self.capture_html_file_paths

        if self.capture_changed_html_files:
            # Add Pull request changed/added HTML files to `to_capture_list`
            changed_files = self._get_pull_request_changed_files()
            to_capture_list += changed_files

        # get Image Upload Service Class and Initialize it
        image_upload_service = self._get_image_upload_service()(
            self.repository,
            self.pull_request_number
        )

        for item in set(to_capture_list):
            display_name = item
            # Generate Image Filename
            filename = self._get_image_filename(display_name)
            # Capture Screenshot
            image_data = self._capture_screenshot(filename, item)
            # Add Image to Uploader Service
            image_upload_service.add(display_name, filename, image_data)

        print_message('Upload Screenshots', message_type='group')
        uploaded_images = image_upload_service.upload()
        print_message('', message_type='endgroup')

        # If any screenshot is uploaded comment the screenshots to the Pull Request
        if uploaded_images:
            print_message('Comment Website Screen Capture', message_type='group')
            self._comment_screenshots(uploaded_images)
            print_message('', message_type='endgroup')


if __name__ == '__main__':
    # Default environment variable from GitHub
    # https://docs.github.com/en/actions/configuring-and-managing-workflows/using-environment-variables
    event_path = os.environ['GITHUB_EVENT_PATH']
    repository = os.environ['GITHUB_REPOSITORY']
    event_name = os.environ['GITHUB_EVENT_NAME']

    # User inputs from workflow
    upload_to = os.environ['INPUT_UPLOAD_TO']
    capture_changed_html_files = os.environ['INPUT_CAPTURE_CHANGED_HTML_FILES']
    capture_html_file_paths = os.environ['INPUT_CAPTURE_HTML_FILE_PATHS']
    capture_urls = os.environ['INPUT_CAPTURE_URLS']

    # Token provided by the workflow run.
    token = (
        os.environ.get('GITHUB_TOKEN') or
        os.environ.get('INPUT_GITHUB_TOKEN')
    )

    # If the workflow was not triggered by a pull request
    # Exit the script with code 1.
    if event_name != 'pull_request':
        print_message(
            'This action only works for pull request event',
            message_type='error'
        )
        sys.exit(1)

    # Group: Website Screen Capture
    print_message('Website Screen Capture', message_type='group')

    # Initialize the Website Screen Capture
    capture = WebsiteScreenshot(
        token,
        repository,
        upload_to,
        event_path,
        capture_changed_html_files,
        capture_html_file_paths=capture_html_file_paths,
        capture_urls=capture_urls
    )
    # Run Website Screen Capture
    capture.run()

    print_message('', message_type='endgroup')
