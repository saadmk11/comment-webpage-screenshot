import json
import os
import subprocess
from functools import cached_property

import requests

import image_upload_services


class WebsiteScreenshot:

    GITHUB_API_URL = 'https://api.github.com'

    def __init__(self, token, repository, upload_to, event_path):
        self.token = token
        self.repository = repository
        self.upload_to = upload_to
        self.pull_request_number = self._get_pull_request_number(event_path)

    @staticmethod
    def _get_pull_request_number(event_path):
        """Gets pull request number from `GITHUB_EVENT_PATH`"""
        with open(event_path, 'r') as json_file:
            # This is just a webhook payload available to the Action
            data = json.load(json_file)
            number = data['number']

        return number

    @staticmethod
    def _take_screenshot(filename, url_or_file_path):
        """Takes a screenshot of websites"""
        launch_options = {"args": ["--no-sandbox"]}
        screenshot_capture_command = [
            "capture-website",
            "--launch-options",
            f"{json.dumps(launch_options)}",
            "--full-page",
            url_or_file_path
        ]
        return subprocess.check_output(screenshot_capture_command)

    @cached_property
    def _request_headers(self):
        """Get headers for GitHub API request"""
        return {
            'Accept': 'application/vnd.github.v3+json',
            'authorization': 'Bearer {token}'.format(token=self.token)
        }

    def _comment_screenshots(self, images):
        """Comments Screenshots to the pull request"""
        owner, repo = self.repository.split('/')
        string_data = 'Here are the Screenshots after the Latest Changes\n'

        for image in images:
            filename, url = image['filename'], image['url']
            string_data += f'![{filename}]({url})\n'

        comment_url = (
            f'{self.GITHUB_API_URL}/repos/{owner}/{repo}/'
            f'issues/{self.pull_request_number}/comments'
        )
        data = {
            'body': string_data,
            'owner': owner,
            'repo': repo,
            'issue_number': self.pull_request_number,
        }
        response = requests.post(
            comment_url,
            headers=self._request_headers,
            data=data
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
            return image_upload_services.ImgurClient()
        return NotImplemented

    def run(self):
        image_upload_service = self._get_image_upload_service()
        urls = ['https://www.google.com', 'https://www.facebook.com']
        images = []

        for url in urls:
            filename = f'PR #{self.pull_request_number}--{url}.png'
            image_data = self._take_screenshot(filename, url)
            image_url = image_upload_service.upload(filename, image_data)

            if image_url:
                images.append(
                    {
                        'filename': filename,
                        'url': image_url
                    }
                )
        self._comment_screenshots(images)


def print_message(message, message_type=None):
    """Helper function to print colorful outputs in GitHub Actions shell"""
    # https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions
    if not message_type:
        return subprocess.run(['echo', f'{message}'])

    if message_type == 'endgroup':
        return subprocess.run(['echo', '::endgroup::'])

    return subprocess.run(['echo', f'::{message_type}::{message}'])


if __name__ == '__main__':
    # Default environment variable from GitHub
    # https://docs.github.com/en/actions/configuring-and-managing-workflows/using-environment-variables
    event_path = os.environ['GITHUB_EVENT_PATH']
    repository = os.environ['GITHUB_REPOSITORY']
    event_name = os.environ['GITHUB_EVENT_NAME']

    # User inputs from workflow
    upload_to = os.environ['INPUT_UPLOAD_TO']

    # Token provided by the workflow run.
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('INPUT_GITHUB_TOKEN')

    # Group: Website Screen Capture
    print_message('Website Screen Capture', message_type='group')

    # Initialize the Website Screen Capture
    capture = WebsiteScreenshot(
        token,
        repository,
        upload_to,
        event_path
    )
    # Run Website Screen Capture
    capture.run()

    print_message('', message_type='endgroup')