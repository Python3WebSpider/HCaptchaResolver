from environs import Env

env = Env()
env.read_env()

CAPTCHA_RESOLVER_API_URL = 'https://api.yescaptcha.com/createTask'
CAPTCHA_RESOLVER_API_KEY = env.str('CAPTCHA_RESOLVER_API_KEY')

CAPTCHA_DEMO_URL = 'https://democaptcha.com/demo-form-eng/hcaptcha.html'

CAPTCHA_ENTIRE_IMAGE_FILE_PATH = 'captcha_entire_image.png'
CAPTCHA_SINGLE_IMAGE_FILE_PATH = 'captcha_single_image_%s.png'
CAPTCHA_RESIZED_IMAGE_FILE_PATH = 'captcha_resized_image.png'
