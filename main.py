import json
import os
import subprocess

import image_upload_services


class WebsiteScreenshot:

    def run(self):
        launch_options = {"args": ["--no-sandbox"]}
        url = "https://google.com"
        output_filename = 'screenshot2.png'
        screenshot_capture_command = [
            "capture-website",
            "--launch-options",
            f"{json.dumps(launch_options)}",
            "--full-page",
            url
        ]
        image_data = subprocess.check_output(screenshot_capture_command)

        client = image_upload_services.ImgurClient()
        client.upload(output_filename, image_data)

if __name__ == '__main__':
    a = WebsiteScreenshot()
    a.run()
