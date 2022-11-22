import requests
from bs4 import BeautifulSoup

authPage = requests.get('https://login.kundelik.kz/login')

soup = BeautifulSoup(authPage.text, 'html.parser')
CaptchaInput = soup.find('img', {'class': 'captcha__image'}).get('src')
CaptchaId = soup.find('input', {'name': 'Captcha.Id'}).get('value')
print(CaptchaInput, CaptchaId)