import json
import os
import subprocess
import sys
import glob
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

    GITHUB_API_URL = 'https://api.github.com'

    def __init__(self, configuration):
        self.configuration = configuration

    @cached_property
    def _request_headers(self):
        """Get headers for GitHub API request"""
        return {
            'Accept': 'application/vnd.github.v3+json',
            'authorization': f'Bearer {self.configuration.GITHUB_TOKEN}'
        }

    def _comment_screenshots(self, images):
        """Comments Screenshots to the pull request"""
        string_data = '## Here are the Screenshots after the Latest Changes\n\n'

        for image in images:
            file_path, filename, url = (
                image['file_path'], image['filename'], image['url']
            )
            string_data += f'### {file_path}\n![{filename}]({url})\n'

        comment_url = (
            f'{self.GITHUB_API_URL}/repos/{self.configuration.GITHUB_REPOSITORY}/'
            f'issues/{self.configuration.GITHUB_PULL_REQUEST_NUMBER}/comments'
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
                'Error while trying to create a comment. '
                'GitHub API returned error response for '
                f'{self.configuration.GITHUB_REPOSITORY}, '
                f'status code: {response.status_code}'
            )
            print_message(msg, message_type='error')

    def _get_image_upload_service(self):
        """Get image upload service"""
        if self.configuration.UPLOAD_TO == self.configuration.UPLOAD_SERVICE_IMGUR:
            return ImgurImageUploadService
        elif self.configuration.UPLOAD_TO == self.configuration.UPLOAD_SERVICE_GITHUB_BRANCH:
            return GitHubBranchImageUploadService
        else:
            return NotImplemented

    def _get_image_filename(self, file_path):
        """Generate Filename from url or file path"""
        return (
            f'pr-{self.configuration.GITHUB_PULL_REQUEST_NUMBER}-{file_path}'
            f'-{int(time.time())}.png'
        ).replace('/', '-').replace(' ', '')

    def run(self):

        # Get Image Upload Service Class and Initialize it
        image_upload_service = self._get_image_upload_service()(
            self.configuration
        )

        for pattern in set(self.configuration.IMAGES):
            files_paths = glob.glob(pattern, recursive=True)
            for file_path in files_paths:
                # Generate Image Filename
                filename = self._get_image_filename(file_path)
                image_upload_service.add(file_path, filename, image_data=open(file_path, "rb"))

        uploaded_images = image_upload_service.upload()

        # If any screenshot is uploaded comment the screenshots to the Pull Request
        if uploaded_images:
            print_message('Comment Webpage Screenshot', message_type='group')
            self._comment_screenshots(uploaded_images)
            print_message('', message_type='endgroup')


if __name__ == '__main__':
    print_message('Parse Configuration', message_type='group')
    environment = os.environ
    configuration = Configuration.from_environment(environment)
    print_message('', message_type='endgroup')

    # If the workflow was not triggered by a pull request
    # Exit the script with code 1.
    if (
        configuration.GITHUB_EVENT_NAME
        not in configuration.SUPPORTED_EVENT_NAMES
    ):
        print_message(
            'This action only works for '
            f'"{configuration.SUPPORTED_EVENT_NAMES}" event(s)',
            message_type='error'
        )
        sys.exit(1)

    # Initialize the Webpage Screenshot Action
    action = WebpageScreenshotAction(configuration)
    # Run Action
    action.run()
