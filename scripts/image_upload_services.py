import subprocess
import time

import requests

from helpers import print_message


class ImageUploadServiceBase:
    """Base Class for All Image Upload Services"""

    def __init__(self, repository, pull_request_number):
        self.files_to_upload = []
        self.repository = repository
        self.pull_request_number = pull_request_number

    def add(self, display_name, filename, image_data):
        self.files_to_upload.append(
            {
                'display_name': display_name,
                'filename': filename,
                'data': image_data
            }
        )

    def upload(self):
        """
        Main Method to Upload Images.

        All Child Classes Should Implement The `upload` Method
        Must return a list of dictionaries

        [{
            'display_name': display_name,
            'filename': filename,
            'url': image_url
        }]
        """
        return NotImplemented


class ImgurImageUploadService(ImageUploadServiceBase):
    """Service to Upload Images to Imgur"""

    def upload_single_image(self, filename, image_data):
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

    def upload(self):
        """Upload Images to Imgur"""
        image_urls = []

        for file in self.files_to_upload:
            filename = file['filename']
            image_url = self.upload_single_image(filename, file['data'])
            if image_url:
                image_urls.append(
                    {
                        'display_name': file['display_name'],
                        'filename': filename,
                        'url': image_url
                    }
                )
                # Sleep for 2 seconds after each successful image upload
                time.sleep(10)
        return image_urls


class GitHubBranchImageUploadService(ImageUploadServiceBase):
    new_branch = 'website-screenshots-action-branch'
    username = 'github-actions[bot]'
    email = 'github-actions[bot]@users.noreply.github.com'
    git_commit_author = f'{username} <{email}>'

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
        print_message('', message_type='endgroup')

    def _push_images(self):
        """Create and push a new branch with the changes"""
        print_message('Push Screenshots to GitHub Branch', message_type='group')
        # Use timestamp to ensure uniqueness of the new branch

        subprocess.run(['git', 'add', 'website-screenshots/'])
        subprocess.run(
            [
                'git', 'commit',
                f'--author={self.git_commit_author}',
                '-m',
                '[website-screenshots-action] '
                f'Added Screenshots for PR #{self.pull_request_number}'
            ]
        )
        subprocess.run(
            ['git', 'push', '-u', 'origin', self.new_branch]
        )
        print_message('', message_type='endgroup')
        return self.new_branch

    def _get_github_image_url(self, filename, new_branch):
        """Get GitHub Image URL"""
        return (
            f'https://raw.githubusercontent.com/{self.repository}/'
            f'{new_branch}/website-screenshots/{filename}'
        )

    def upload(self):
        """Upload Images to a GitHub Branch"""
        image_urls = []

        if not self.files_to_upload:
            return image_urls

        # Create and push the changes to a new branch
        new_branch = self._push_images()

        for file in self.files_to_upload:
            filename = file['filename']
            image_urls.append(
                {
                    'display_name': file['display_name'],
                    'filename': filename,
                    'url': self._get_github_image_url(
                        filename, new_branch
                    )
                }
            )
        return image_urls
