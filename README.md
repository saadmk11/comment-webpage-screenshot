# Website Screen Capture

Website Screen Capture is a GitHub Action that takes a screenshot of
webpages or html file paths and uploads it to an Image Upload Service
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
          # Optional, the action will create a new branch and
          # upload the screenshots to that branch.
          upload_to: github_branch  # Or, imgur
          # Optional, the action will capture screenshots
          # of all the changed html files on the pull request.
          capture_changed_html_files: yes  # Or, no
          # Optional, the action will capture screenshots
          # of the html files provided in this input.
          # Comma seperated file paths are accepted
          capture_html_file_paths: "/pages/index.html, about.html"
          # Optional, the action will capture screenshots
          # of the URLs provided in this input.
          # You can add URLs of your development server or
          # run the server in the previous step
          # and add that URL here (For Example: http://172.17.0.1:8000/).
          # Comma seperated URLs are accepted.
          capture_urls: "https://dev.example.com, https://dev.example.com/about.html"
          # Optional
          github_token: {{ secrets.MY_GITHUB_TOKEN }}
```

## Available Image Upload Services

These are the currently available image upload services.
As GitHub Does not allow us to upload images to a comment using the API
we need to rely on other services to host the screenshots.

**If you want to add/use a different image upload service, feel free create a new issue/pull request.**

### Imgur

If the value of `upload_to` input is `imgur` then the screenshots will be uploaded to Imgur.
Keep in mind that the screenshots will be **public** and anyone can see them.
Imgur also has a rate limit of how many images can be uploaded per hour.
Refer to Imgur's [Rate Limits](https://api.imgur.com/#limits) Docs for more details.
This is suitable for **small open source** repositories.

Please refer to Imgur terms of service [here](https://imgur.com/tos)

### GitHub Branch (Default)

If the value of `upload_to` input is `github_branch` then the screenshots will be pushed
to a GitHub branch created by the action on your repository.
The screenshots on the comments will reference the Images pushed to this branch.

This is used by default on this action.
This is suitable for **open source** and **private** repositories.

## Examples

You Can find some example usecases of this action here: [Example Projects](https://github.com/saadmk11/comment-website-screenshot/tree/main/examples)

Here are some comments created by this action on the Example Project:

![Screenshot from 2021-11-18 21-32-20](https://user-images.githubusercontent.com/24854406/142447670-e61115ec-444a-4869-b133-2b9969b681de.png)
![screencapture-github-saadmk11-django-demo-pull-11-2021-11-18-21_31_00](https://user-images.githubusercontent.com/24854406/142447685-22aee5cf-49f1-4c50-8908-ccad5c56514b.png)

# License

The code in this project is released under the [GNU GENERAL PUBLIC LICENSE Version 3](LICENSE).
