import base64
import subprocess
import time
from functools import cached_property

import requests

from helpers import print_message


class ImageUploadServiceBase:
    """Base Class for All Image Upload Services"""

    def __init__(self, configuration):
        self.configuration = configuration
        self.images_to_upload = []
        self.uploaded_images = []

    def _upload_single_image(self, filename, image_data):
        """
        Main Method to Upload a Single Images.

        All Child Classes May Implement The `_upload_single_image` Method
        Must return a image URL or None
        """
        return None

    def add(self, file_path, filename, image_data):
        self.images_to_upload.append(
            {"file_path": file_path, "filename": filename, "data": image_data}
        )

    def upload(self):
        """
        Main Method to Upload Images.

        Child Classes May Override The `upload` Method
        Must return a list of dictionaries

        [{
            'file_path': file_path,
            'filename': filename,
            'url': image_url
        }]
        """
        print_message("Upload Screenshots", message_type="group")

        for file in self.images_to_upload:
            filename = file["filename"]
            image_url = self._upload_single_image(filename, file["data"])
            if image_url:
                self.uploaded_images.append(
                    {
                        "file_path": file["file_path"],
                        "filename": filename,
                        "url": image_url,
                    }
                )
                # Sleep for 2 seconds after each successful image upload
                time.sleep(2)

        print_message("", message_type="endgroup")

        return self.uploaded_images


class ImgurImageUploadService(ImageUploadServiceBase):
    """Service to Upload Images to Imgur"""

    IMGUR_API_URL = "https://api.imgur.com/3/upload"

    def _upload_single_image(self, filename, image_data):
        """Upload a Single Image to Imgur using Imgur API"""
        response = requests.post(
            self.IMGUR_API_URL,
            files={
                "image": image_data,
            },
            data={"name": filename},
        )

        data = response.json()

        if response.status_code == 200 and data["success"]:
            link = data["data"]["link"]
            print_message(f'Image "{filename}" Uploaded to "{link}"')
            return link
        else:
            print_message(
                f'Failed to Upload Image "{filename}". '
                f"Status Code: {response.status_code}"
            )
            return None


class GitHubBranchImageUploadService(ImageUploadServiceBase):
    """Service to Upload Images to GitHub Branch"""

    GITHUB_API_URL = "https://api.github.com"
    BRANCH_NAME = "webpage-screenshot-action-branch"
    IMAGE_UPLOAD_DIRECTORY = "webpage-screenshots"
    AUTHOR_NAME = "github-actions[bot]"
    AUTHOR_EMAIL = "github-actions[bot]@users.noreply.github.com"

    @cached_property
    def _request_headers(self):
        """Get headers for GitHub API request"""
        return {
            "Accept": "application/vnd.github.v3+json",
            "authorization": f"Bearer {self.configuration.GITHUB_TOKEN}",
        }

    def _setup_git_branch(self):
        """Set Up Git Branch"""
        print_message("Setup GitHub Branch", message_type="group")
        subprocess.run(["git", "config", "user.name", self.AUTHOR_NAME])
        subprocess.run(["git", "config", "user.email", self.AUTHOR_EMAIL])

        subprocess.run(
            ["git", "fetch", "origin", "--prune", "--unshallow"],
        )

        remote_branches = subprocess.check_output(
            ["git", "branch", "-r"],
        )

        if self.BRANCH_NAME not in str(remote_branches):
            subprocess.run(["git", "checkout", "-b", self.BRANCH_NAME])
            subprocess.run(["git", "push", "-u", "origin", self.BRANCH_NAME])
        else:
            print_message(f'Branch "{self.BRANCH_NAME}" Already Exists')
        print_message("", message_type="endgroup")

    def _get_github_image_url(self, filename):
        """Get GitHub Image URL"""
        return (
            f"https://github.com/{self.configuration.GITHUB_REPOSITORY}/raw"
            f"/{self.BRANCH_NAME}/{self.IMAGE_UPLOAD_DIRECTORY}/{filename}"
        )

    def _upload_single_image(self, filename, image_data):
        url = (
            f"{self.GITHUB_API_URL}/repos/{self.configuration.GITHUB_REPOSITORY}"
            f"/contents/{self.IMAGE_UPLOAD_DIRECTORY}/{filename}"
        )
        data = {
            "message": (
                "[webpage-screenshot-action] Added Screenshots for "
                f"PR #{self.configuration.GITHUB_PULL_REQUEST_NUMBER}"
            ),
            "content": base64.b64encode(image_data).decode("utf-8"),
            "branch": self.BRANCH_NAME,
            "author": {"name": self.AUTHOR_NAME, "email": self.AUTHOR_EMAIL},
            "committer": {"name": self.AUTHOR_NAME, "email": self.AUTHOR_EMAIL},
        }

        response = requests.put(url, headers=self._request_headers, json=data)

        if response.status_code in [200, 201]:
            link = self._get_github_image_url(filename)
            print_message(f'Image "{filename}" Uploaded to "{link}"')
            return link
        else:
            # API should return 201, otherwise show error message
            msg = (
                f'Error while trying to upload "{filename}" to github. '
                "GitHub API returned error response for "
                f"{self.configuration.GITHUB_REPOSITORY},"
                f"status code: {response.status_code}"
            )
            print_message(msg, message_type="error")
            return None

    def upload(self):
        """Upload Images to a GitHub Branch"""
        if not self.images_to_upload:
            return []

        # Create a new branch
        self._setup_git_branch()

        return super().upload()
