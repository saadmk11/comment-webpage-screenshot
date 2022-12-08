import glob
import os
import sys
from functools import cached_property
from itertools import islice

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

    def _comment_screenshots(self, images):
        """Comments Screenshots to the pull request"""
        run_url = (
            f"https://github.com/{self.configuration.GITHUB_REPOSITORY}/"
            f"actions/runs/{self.configuration.GITHUB_RUN_ID}"
        )

        comment_body = f"{self.configuration.CUSTOM_ATTACHMENT_MSG} `{self.configuration.GITHUB_SHA}`. \
            _You can inspect the workflow run [here]({run_url})_. \n\n"

        for image in sorted(images, key=lambda image: image["filename"]):
            file_path, filename, url = (
                image["file_path"],
                image["filename"],
                image["url"],
            )
            has_extension = filename[-4:]

            if any(f in has_extension for f in ["png", "jpg", "jpeg", "webp", "gif"]):
                gh_media_url_embedding = f"<kbd>![{filename}]({url})</kbd>"

            else:
                gh_media_url_embedding = url

            comment_body += f"### {file_path}\n\n{gh_media_url_embedding}\n"

        comment_url = (
            f"{self.GITHUB_API_URL}/repos/{self.configuration.GITHUB_REPOSITORY}/"
            f"issues/{self.configuration.GITHUB_PULL_REQUEST_NUMBER}/comments"
        )

        response = requests.post(
            comment_url, headers=self._request_headers, json={"body": comment_body}
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
        else:
            if self.configuration.EDIT_PREVIOUS_COMMENT:
                comment = response.json()
                self._deprecate_previous_if_any(
                    latest_issue_url=comment["issue_url"],
                    latest_comment_url=comment["html_url"],
                )

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
            (f"pr-{self.configuration.GITHUB_PULL_REQUEST_NUMBER}-{file_path}")
            .replace("/", "-")
            .replace(" ", "")
        )

    def _deprecate_previous_if_any(
        self, latest_issue_url: str, latest_comment_url: str
    ):
        """Tell the previous comment about the new one."""
        deprecation_notice_body = f"__DEPRECATED__: _This screenshot is no longer up-to-date. The latest version can be found [here]({latest_comment_url})_."

        url_list_comments_in_issue = (
            f"{self.GITHUB_API_URL}/repos/{self.configuration.GITHUB_REPOSITORY}/"
            f"issues/{self.configuration.GITHUB_PULL_REQUEST_NUMBER}/comments"
        )

        response = requests.get(
            url_list_comments_in_issue, headers=self._request_headers
        )

        if response.status_code != 200:
            print_message(
                "Unable to list previous comments; we will thus not attempt to deprecate any previous comment"
            )
            return

        elif comments := response.json():
            # get the latest 2 comments from the bot if any
            from_bot_same_issue_or_pr = filter(
                lambda c: c["user"]["login"] == "github-actions[bot]"
                and self.configuration.CUSTOM_ATTACHMENT_MSG in c["body"]
                and c["issue_url"] == latest_issue_url,
                comments,
            )
            last_comments = list(
                islice(
                    sorted(
                        from_bot_same_issue_or_pr,
                        key=lambda c: c["created_at"],
                        reverse=True,
                    ),
                    2,
                )
            )

            if len(last_comments) != 2:
                print_message(
                    "This is the latest commented batch of screenshots, you're all good!"
                )

            else:
                edit_past_comment_url = (
                    f"{self.GITHUB_API_URL}/repos/{self.configuration.GITHUB_REPOSITORY}/"
                    f"issues/comments/{last_comments[1]['id']}"
                )
                response = requests.patch(
                    edit_past_comment_url,
                    headers=self._request_headers,
                    json={"body": deprecation_notice_body},
                )

    def run(self):

        # Get Image Upload Service Class and Initialize it
        image_upload_service = self._get_image_upload_service()(self.configuration)

        for pattern in set(self.configuration.IMAGES):
            files_paths = glob.glob(pattern, recursive=True)
            for file_path in files_paths:
                # Generate Image Filename
                filename = self._get_image_filename(file_path)
                image_data = open(file_path, "rb").read()
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
