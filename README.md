# Website Screen Capture

Website Screen Capture is a GitHub Action that takes a screenshot of
webpages or html file paths and uploads it to a Image Upload Service
and then comments the screenshots on the pull request that triggered the action.

**Note:** This Action Only Works on a Pull Request.

## Workflow inputs

These are the inputs that can be provided on the workflow.

| Name | Required | Description | Default |
|------|----------|-------------|---------|
| `upload_to` | No | Image Upload Service Name (Options are: `github_branch`, `imgur`) **[More Details](#available-image-upload-services)** | `github_branch` |
| `capture_changed_html_files` | No | Enable or Disable Screenshot Capture for Changed HTML Files on the Pull Request (Options are: `yes`, `no`) | `yes` |
| `capture_html_file_paths` | No | Comma Seperated paths to the HTML files to be captured (Example: `/pages/index.html, about.html`) | `null` |
| `capture_urls` | No | Comma Seperated URLs to be captured (Example: `https://dev.example.com, https://dev.example.com/about.html`) | `null` |
| `github_token` | No | `GITHUB_TOKEN` provided by the workflow run or Personal Access Token (PAT) | `github.token` |

## Example Workflow

```yaml
name: Capture Webpage Screenshot

on:
  pull_request:
    types: [opened, reopened, synchronize]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Capture Webpage Screenshot
        uses: saadmk11/comment-website-screenshot@main
        with:
          # Optional, the action will create a new branch and push the screenshots to the branch.
          upload_to: github_branch
          # Optional, the action will capture the screenshots for all the changed html files on the pull request.
          capture_changed_html_files: yes
          # Optional, the action will capture the screenshots of the html files provided in the capture_html_file_paths input.
          capture_html_file_paths: "/pages/index.html, about.html"
          # Optional, the action will capture the screenshots of the urls provided in the capture_urls input.
          capture_urls: "https://dev.example.com, https://dev.example.com/about.html"
          # Optional
          github_token: {{ secrets.MY_GITHUB_TOKEN }}
```

## Available Image Upload Services

These are the currently available image upload services.
As GitHub Does not allow us to upload images to a comment using the API
we need to rely on other services to host the screenshots.

**If you want to add/use a different image upload service, please create a new issue/pull request.**

### Imgur

If the value of `upload_to` input is `imgur` then the screenshots will be uploaded to Imgur.
Keep in mind that the screenshots will be **public** and anyone can see them.
Imgur also has a rate limit of how many images can be uploaded per hour.
Refer to Imgur 's [Rate Limits](https://api.imgur.com/#limits) Docs for more details.
This is suitable for **small open source** repositories.

Please refer to Imgur terms of service [here](https://imgur.com/tos)

### GitHub Branch (Default)

If the value of `upload_to` input is `github_branch` then the screenshots will be pushed
to a GitHub branch created by the action on your repository.
The screenshots on the comments will reference the Images pushed to this branch.

This is used by default on this action.
This is suitable for **open source** and **private** repositories.
