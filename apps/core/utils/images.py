import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def save_temporary_form_image(image_file):
    file_name = f"temp_{image_file.name}"
    return default_storage.save(f"temp/{file_name}", ContentFile(image_file.read()))


def get_random_user_image():
    response = requests.get("https://randomuser.me/api/")
    if response.status_code == 200:
        data = response.json()
        image_url = data["results"][0]["picture"]["large"]
        return image_url
    return None
