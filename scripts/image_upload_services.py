import subprocess

import requests

from helpers import print_message


class ImageUploadServiceBase:

    def __init__(self, repository, pull_request_number):
        self.files_to_upload = []
        self.repository = repository
        self.pull_request_number = pull_request_number

    def add(self, filename, image_data):
        self.files_to_upload.append(
            {'filename': filename, 'data': image_data}
        )

    def upload(self):
        return NotImplemented


class ImgurImageUploadService(ImageUploadServiceBase):

    def upload_single_image(self, name, image_data):
        response = requests.post(
            'https://api.imgur.com/3/upload',
            files={
                "image": image_data,
            },
            data={
                'name': name
            }
        )
        data = response.json()

        if response.status_code == 200 and data['success']:
            link = data['data']['link']
            print_message(f'Image "{name}" Uploaded to "{link}"')
            return link
        else:
            print_message(
                f'Image "{name}" Upload Failed. '
                f'Status Code: {response.status_code}'
            )

    def upload(self):
        image_urls = []
        for file in self.files_to_upload:
            filename = file['filename']
            image_url = self.upload_single_image(
                filename, file['data']
            )
            if image_url:
                image_urls.append(
                    {
                        'filename': filename,
                        'url': image_url
                    }
                )
        return image_urls


class GitHubBranchImageUploadService(ImageUploadServiceBase):

    def _create_new_branch(self):
        """Create and push a new branch with the changes"""
        # Use timestamp to ensure uniqueness of the new branch
        new_branch = 'website-screenshots-action-branch'
        username = 'github-actions[bot]'
        email = 'github-actions[bot]@users.noreply.github.com'
        git_commit_author = f'{username} <{email}>'

        subprocess.run(['git', 'config', 'user.name', username])
        subprocess.run(['git', 'config', 'user.email', email])

        subprocess.run(
            ['git', 'fetch', 'origin', '--prune', '--unshallow'],
        )

        remote_branches = subprocess.check_output(
            ['git', 'branch', '-r'],
        )

        if new_branch in str(remote_branches):
            print('Branch already exists...')
            subprocess.run(
                ['git', 'checkout', new_branch]
            )
        else:
            print('Branch Does not exist...')
            subprocess.run(
                ['git', 'checkout', '-b', new_branch]
            )

        subprocess.run(['git', 'add', '.'])
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
        return new_branch

    def _get_github_image_url(self, filename, new_branch):
        return (
            f'https://raw.githubusercontent.com/{self.repository}/'
            f'{new_branch}/website-screenshots/{filename}'
        )

    def upload(self):
        new_branch = self._create_new_branch()
        image_urls = []

        for file in self.files_to_upload:
            filename = file['filename']
            image_urls.append(
                {
                    'filename': filename,
                    'url': self._get_github_image_url(
                        filename, new_branch
                    )
                }
            )
        return image_urls
