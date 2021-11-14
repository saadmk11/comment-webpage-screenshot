import requests

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
            return data['data']['link']
