import subprocess
import time
from functools import cached_property

import requests

from helpers import print_message


class ImageUploadServiceBase:
    """Base Class for All Image Upload Services"""

    def __init__(self, repository, pull_request_number):
        self.files_to_upload = []
        self.repository = repository
        self.pull_request_number = pull_request_number
        self.image_urls = []

    def add(self, display_name, filename, image_data):
        self.files_to_upload.append(
            {
                'display_name': display_name,
                'filename': filename,
                'data': image_data
            }
        )

    def _upload_single_image(self, filename, image_data):
        """
        Main Method to Upload a Single Images.

        All Child Classes May Implement The `_upload_single_image` Method
        Must return a image URL or None
        """
        return None

    def upload(self):
        """
        Main Method to Upload Images.

        Child Classes May Override The `upload` Method
        Must return a list of dictionaries

        [{
            'display_name': display_name,
            'filename': filename,
            'url': image_url
        }]
        """
        for file in self.files_to_upload:
            filename = file['filename']
            image_url = self._upload_single_image(filename, file['data'])
            if image_url:
                self.image_urls.append(
                    {
                        'display_name': file['display_name'],
                        'filename': filename,
                        'url': image_url
                    }
                )
                # Sleep for 2 seconds after each successful image upload
                time.sleep(2)

        return self.image_urls


class ImgurImageUploadService(ImageUploadServiceBase):
    """Service to Upload Images to Imgur"""

    def _upload_single_image(self, filename, image_data):
        """Upload a Single Image to Imgur using Imgur API"""
        response = requests.post(
            'https://api.imgur.com/3/upload',
            files={
                "image": image_data,
            },
            data={
                'name': filename
            }
        )

        data = response.json()

        if response.status_code == 200 and data['success']:
            link = data['data']['link']
            print_message(f'Image "{filename}" Uploaded to "{link}"')
            return link
        else:
            print_message(
                f'Failed to Upload Image "{filename}". '
                f'Status Code: {response.status_code}'
            )
            return None


class GitHubBranchImageUploadService(ImageUploadServiceBase):

    GITHUB_API_URL = 'https://api.github.com'
    new_branch = 'website-screenshots-action-branch'
    username = 'github-actions[bot]'
    email = 'github-actions[bot]@users.noreply.github.com'
    git_commit_author = f'{username} <{email}>'

    def __init__(self, repository, pull_request_number, github_token):
        self.github_token = github_token
        super().__init__(repository, pull_request_number)

    @cached_property
    def _request_headers(self):
        """Get headers for GitHub API request"""
        return {
            'Accept': 'application/vnd.github.v3+json',
            'authorization': f'Bearer {self.github_token}'
        }

    def _setup_git_branch(self):
        """Set Up Git Branch"""
        print_message('Setup GitHub Branch', message_type='group')
        subprocess.run(['git', 'config', 'user.name', self.username])
        subprocess.run(['git', 'config', 'user.email', self.email])

        subprocess.run(
            ['git', 'fetch', 'origin', '--prune', '--unshallow'],
        )

        remote_branches = subprocess.check_output(
            ['git', 'branch', '-r'],
        )

        if self.new_branch in str(remote_branches):
            subprocess.run(
                ['git', 'checkout', self.new_branch]
            )
        else:
            subprocess.run(
                ['git', 'checkout', '-b', self.new_branch]
            )
        subprocess.run(
            ['git', 'push', '-u', 'origin', self.new_branch]
        )
        print_message('', message_type='endgroup')

    # def _push_images(self):
    #     """Create and push a new branch with the changes"""
    #     print_message('Push Screenshots to GitHub Branch', message_type='group')
    #     # Use timestamp to ensure uniqueness of the new branch
    #
    #     subprocess.run(['git', 'add', 'website-screenshots/'])
    #     subprocess.run(
    #         [
    #             'git', 'commit',
    #             f'--author={self.git_commit_author}',
    #             '-m',
    #             '[website-screenshots-action] '
    #             f'Added Screenshots for PR #{self.pull_request_number}'
    #         ]
    #     )
    #     subprocess.run(
    #         ['git', 'push', '-u', 'origin', self.new_branch]
    #     )
    #     print_message('', message_type='endgroup')
    #     return self.new_branch

    def _upload_single_image(self, filename, image_data):
        url = (
            f'{self.GITHUB_API_URL}/repos/{self.repository}'
            f'/contents/website-screenshots/{filename}'
        )
        print(url)
        data = {
            'message': (
                '[website-screenshots-action] '
                f'Added Screenshots for PR #{self.pull_request_number}'
            ),
            'content': str(image_data),
            'branch': self.new_branch,
            'author': {
                'name': self.username,
                'email': self.email
            },
            'committer': {
                'name': self.username,
                'email': self.email
            }
        }
        print(data)

        response = requests.post(
            url,
            headers=self._request_headers,
            json=data
        )

        print(response.json())
        print(response.status_code)

        if response.status_code in [200, 201]:
            return response.json()['download_url']
        else:
            # API should return 201, otherwise show error message
            msg = (
                f'Error while trying to upload "{filename}" to github. '
                f'GitHub API returned error response for '
                f'{self.repository}, status code: {response.status_code}'
            )
            print_message(msg, message_type='error')
            return None

    # def _get_github_image_url(self, filename, new_branch):
    #     """Get GitHub Image URL"""
    #     return (
    #         f'https://github.com/{self.repository}/raw'
    #         f'/{new_branch}/website-screenshots/{filename}'
    #     )

    def upload(self):
        """Upload Images to a GitHub Branch"""
        if not self.files_to_upload:
            return self.image_urls

        # Create a new branch
        self._setup_git_branch()

        return super().upload()
