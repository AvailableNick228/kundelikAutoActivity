import json
import os
import requests
import config
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

from sqlalchemy import create_engine, MetaData, Table, String, Integer, Column, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent

engine = create_engine('sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'))

Base = declarative_base()
meta = MetaData(engine)
session = sessionmaker(bind=engine)()


class Person(Base):
    __tablename__ = 'person'

    chatId = Column(Integer, nullable=False, primary_key=True)
    name = Column(Text)
    role = Column(Text,  nullable=False, default='notUser')
    created_on = Column(DateTime, default=datetime.now)
    updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    

class Account(Base):
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    login = Column(Text, nullable=False)
    password = Column(Text,  nullable=False)
    user_id = Column(Integer, nullable=False)
    created_on = Column(DateTime, default=datetime.now)
    updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)


    def getCaptcha(self, session):
        authPage = session.get('https://login.kundelik.kz/login')
        soup = BeautifulSoup(authPage.text, 'html.parser')
        CaptchaImage = soup.find('img', {'class': 'captcha__image'}).get('src')
        CaptchaId = soup.find('input', {'name': 'Captcha.Id'}).get('value')
        if CaptchaImage is None and CaptchaId is None:
            return None
        else:
            return {'CaptchaImage': CaptchaImage, 'CaptchaId': CaptchaId}

    def make_auth(self, session: requests.Session, CaptchaId='', CaptchaInput=''):
        data = {
            'exceededAttempts': False,
            'ReturnUrl': '',
            'FingerprintId': '',
            'login': self.login,
            'password': self.password,
            'Captcha.Input': CaptchaInput,
            'Captcha.Id': CaptchaId
        }
        response = session.post('https://login.kundelik.kz/login', data=data, timeout=100)
        file = open('response.html', 'w', encoding="utf-8")
        file.write(response.text)
        file.close()
        soup = BeautifulSoup(response.text, 'html.parser')
        error = soup.find('div', {'class': 'message'})
        if error and error.text.strip() == 'Пайдаланушы аты немесе құпиясөзде қате бар. Өрістердің дұрыс толтырылуын тексеріңіз.':
            return {'success': False, 'message': '❌ Не правильный логин или пароль, попробуйте снова'}
        else:
            file = open(os.path.join(BASE_DIR, 'cookies/' + self.login + '.json'), 'w')
            file.write(json.dumps(session.cookies.get_dict()))
            file.close()
            return {'success': True,'message': '✅ Успешная авторизация\n🤖 Робот каждые 3 часа проверяет оценки'}

    def auth(self, CaptchaId='', CaptchaInput=''):
        session = requests.Session()

        if CaptchaId != '' and CaptchaInput != '':
            captcha = self.getCaptcha(session)
            if captcha is None:
                return self.make_auth(session)
            else:
                return captcha
        else:
            return self.make_auth(session, CaptchaId, CaptchaInput)

    def send_message_to_user(self, message):
        data = {
            "chat_id": self.user_id,
            "text": message
        }
        requests.get(f"https://api.telegram.org/bot{config.bot_token}/sendMessage", data=data).json()

    def activity(self):
        file = open(os.path.join(BASE_DIR, 'cookies/' + self.login + '.json'), 'r')
        data = json.load(file)
        file.close()
        response = requests.get('https://schools.kundelik.kz/marks.aspx', timeout=50, cookies=data, allow_redirects=False)
        file = open('response.html', 'w', encoding="utf-8")
        file.write(response.text)
        file.close()
        soup = BeautifulSoup(response.text, 'html.parser')

        if soup.find('a', {'href': 'https://login.kundelik.kz/?ReturnUrl=https%3a%2f%2fschools.kundelik.kz%2fmarks.aspx'}):
            self.send_message_to_user('🤖 Робот не смог проверить оценки. Нужно заново добавить аккаунт!')
        else:
            self.send_message_to_user('🤖 Робот проверил оценки')


            

def create_all():
    Base.metadata.create_all(engine)

create_all()