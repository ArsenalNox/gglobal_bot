import httpx
import xml.etree.ElementTree as ET
import logging
import re 
import requests

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean, BigInteger
from sqlalchemy.orm import declarative_base, relationship, backref, Session
from sqlalchemy.engine import URL
from datetime import datetime

from dotenv import load_dotenv
from os import getenv

load_dotenv()

connection_url = URL.create(
    drivername="postgresql",
    username=getenv("POSTGRES_USER"),
    host=getenv("POSTGRES_HOST"),
    port=getenv("POSTGRES_PORT"),
    database=getenv("POSTGRES_DB"),
    password=getenv("POSTGRES_PASSWORD")
)

engine = create_engine(connection_url)
Base = declarative_base()

#TODO: Хранить как-то по-другому, или не тут
dollar_usa_valute_id = 'R01235'

class User(Base):
    """
    Пользователи
    """
    __tablename__ = "users"

    id = Column(Integer(), primary_key=True)
    telegram_id = Column(BigInteger(), unique=True, nullable=False)
    join_date = Column(DateTime(), default=datetime.now())
    last_access = Column(DateTime(), default=datetime.now())
    mailing = relationship('Mailing', backref='author')


    def get_or_create(t_id:int):
        """
        Получить или создать пользователя
        """
        logging.debug(f'Getting user with id {t_id}')

        user = None
        with Session(engine, expire_on_commit=False) as session:
            user = session.query(User).filter_by(telegram_id = t_id).first()

            if not user: 
                user = User(
                    telegram_id = t_id,
                )

                session.add(user)
                session.commit()
                logging.debug("Created new user")

        return user


    def get_all():
        """
        Получить всех пользователей
        """
        with Session(engine, expire_on_commit=False) as session:
            all_users = session.query(User).all()
            return all_users


class Mailing(Base):
    """
    Модель рассылок пользователям
    """
    __tablename__ = 'mailing'

    id = Column(Integer(), primary_key=True)

    #Активна ли работа в scheduler'е
    is_active = Column(Boolean(), default=True) 
    #Айди пользователя и job_id, у пользователя может быть только 1 тайминг
    user_id = Column(Integer(), ForeignKey('users.id'), unique=True)
    #Тайминг срабатывания в формате H:{Час}M:{Минуты}
    timing = Column(String()) #Тайминг рассылки

    def create_or_replace(user_id:int, message_text):
        """
        Создать или заменить подписку
        """
        was_replaced = False

        user = User.get_or_create(user_id)

        found_hours = []
        found_minutes = []
        reply_text = "Интервал"

        if re.match(r'([Кк]ажд)(.)*[\d](\ )час(.*[\d+](\ )мин)?', message_text):
            found_hours = re.findall(r'\d+', message_text)
            reply_text += f'\nКаждый {found_hours[0]} час'
            if len(found_hours) > 1:
                found_minutes = [found_hours[1]]
                reply_text += f' {found_minutes[0]} минут'
                found_hours.pop()

        elif re.match(r'([кК]ажд)([аА-яЯ])+( )[\d]+(\ )мин', message_text):
            found_minutes = re.findall(r'\d+', message_text)
            reply_text += f'\nКаждые {found_minutes[0]} минут'

        else:
            return False, "Не удалось разобрать интервал", None
             
        reply_text += '\nустановлен'
        logging.debug(found_hours)
        logging.debug(found_minutes)

        req_hours = f"H:{found_hours[0]}" if len(found_hours) > 0 else ''
        req_minutes = f"M:{found_minutes[0]}" if len(found_minutes) > 0 else ''
        request = requests.get(f"http://{getenv('SCHEDULER_HOST')}:8081/add_timer/{user.telegram_id}/{req_hours}{req_minutes}")

        if not '200' in request.text:
            False, "Не удалось создать интервал", None
        
        mailing = None

        with Session(engine, expire_on_commit=False) as session:
            mailing = session.query(Mailing).filter_by(user_id=user.id).first()
            if not mailing:
                mailing = Mailing(
                    user_id = user.id,
                    timing = f'{req_hours}{req_minutes}'
                )
                session.add(mailing)

            else:
                mailing.timing = f'{req_hours}{req_minutes}'

            session.commit()
                
        return True, reply_text, mailing


    def get_mailing_of_user(user_id:int):
        """
        Получить подписку пользователя
        """
        with Session(engine) as session:
            mailing = session.query(Mailing).filter_by(user_id=user_id).first()
            if not mailing:
                return None

            else:
                return mailing


    def remove_mailing(user_id:int):
        """
        Удалить подписку
        """
        with Session(engine, expire_on_commit=False) as session:
            try:
                delete_stm = session.query(Mailing).filter_by(user_id=user_id).delete()
                session.commit()
                return True

            except Exception as err:
                logging.error(err)
                return False


class Course(Base): 
    """
    Модель истории курса для USD
    """
    __tablename__ = 'courses'

    id = Column(Integer(), primary_key=True)
    date = Column(DateTime(), default=datetime.now())
    value = Column(Float(), nullable=False)
    valute_code = Column(String(),nullable=False)
    user_id = Column(Integer(), ForeignKey('users.id'))


    def get_current_rate(user_id) -> list[str, str] | None:
        """
        Получить курс доллара с цбрф
        """
        #TODO: dependency injection? с получателем круса 

        logging.debug('Getting exchange rate')

        r = httpx.get('https://www.cbr.ru/scripts/XML_daily.asp')
        if not r.status_code == 200:
            logging.error(f'Failed to get exchange rate, status code: {r.status_code}')
            return None

        tree = ET.fromstring(r.text)
        dollar_data = tree.findall(f'''.//*[@ID='{dollar_usa_valute_id}']''')[0]

        value = dollar_data.find('Value').text.replace(',', '.') 
        char_code = dollar_data.find('CharCode').text.replace(',', '.')

        with Session(engine) as session:
            new_course = Course(
                value = value,
                valute_code = char_code,
                user_id = user_id,
                date=datetime.now()
            )
            session.add(new_course)
            session.commit()

        return value, char_code


    def get_history(user_id):
        """
        История получения курса доллара пользователем
        """
        with Session(engine) as session:
            courses = session.query(Course).filter_by(user_id = User.get_or_create(user_id).id)\
            .order_by(Course.date.desc())\
            .limit(20)
            return courses


Base.metadata.create_all(engine)