import requests

from helpers import print_message


class ImgurClient:
    IMAGE_UPLOAD_URL = 'https://api.imgur.com/3/upload'

    def upload(self, name, image_data):
        response = requests.post(
            self.IMAGE_UPLOAD_URL,
            files={
                "image": image_data,
            },
            data={
                'name': name
            }
        )
        print(response.status_code)
        print(response.json())
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
