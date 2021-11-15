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

    def _create_new_branch(self):
        """Create and push a new branch with the changes"""
        print_message('Push Screenshots to GitHub Branch', message_type='group')
        # Use timestamp to ensure uniqueness of the new branch
        new_branch = 'website-screenshots-action-branch'
        username = 'github-actions[bot]'
        email = 'github-actions[bot]@users.noreply.github.com'
        git_commit_author = f'{username} <{email}>'

        subprocess.run(['git', 'config', 'user.name', username])
        subprocess.run(['git', 'config', 'user.email', email])
        subprocess.run(['git', 'status'])
        subprocess.run(['git', 'diff'])

        subprocess.run(
            ['git', 'fetch', 'origin', '--prune', '--unshallow'],
        )

        remote_branches = subprocess.check_output(
            ['git', 'branch', '-r'],
        )

        if new_branch in str(remote_branches):
            subprocess.run(
                ['git', 'checkout', new_branch]
            )
        else:
            subprocess.run(
                ['git', 'checkout', '-b', new_branch]
            )

        subprocess.run(['git', 'add', 'website-screenshots/'])
        subprocess.run(
            [
                'git', 'commit',
                f'--author={git_commit_author}',
                '-m',
                '[website-screenshots-action] '
                f'Added Screenshots for PR #{self.pull_request_number}'
            ]
        )
        subprocess.run(
            ['git', 'push', '-u', 'origin', new_branch]
        )
        print_message('', message_type='endgroup')
        return new_branch

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
        new_branch = self._create_new_branch()

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
