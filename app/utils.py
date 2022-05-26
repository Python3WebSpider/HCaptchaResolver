from PIL import Image
import base64
from app.settings import CAPTCHA_RESIZED_IMAGE_FILE_PATH


def resize_base64_image(filename, size):
    width, height = size
    img = Image.open(filename)
    new_img = img.resize((width, height))
    new_img.save(CAPTCHA_RESIZED_IMAGE_FILE_PATH)
    with open(CAPTCHA_RESIZED_IMAGE_FILE_PATH, "rb") as f:
        data = f.read()
        encoded_string = base64.b64encode(data)
        return encoded_string.decode('utf-8')
