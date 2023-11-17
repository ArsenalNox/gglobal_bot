import asyncio
import logging
import sys
import requests

from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from kb import main_menu_markup, interval_select_markup, back_to_interval_selection, interval_select_markup_has_mailing
from models import User, Mailing, Course, engine
from datetime import datetime

import re

from bot import bot

router = Router()


@router.message(F.text == 'Назад в меню')
@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    `/start`
    """
    #DONE: Запись пользователя в бд при старте
    
    user = User.get_or_create(message.from_user.id)
    logging.debug(f'User: {user.telegram_id} start')

    await message.answer(
        f"Hello, {hbold(message.from_user.full_name)}!",
        reply_markup=main_menu_markup
        )


@router.message(F.text == 'Получить курс USD')
@router.message(Command('course'))
async def get_course_handler(message: types.Message) -> None:
    """
    Хандлер получения курса доллара
    """
    logging.debug("Getting course")
    course = Course.get_current_rate(User.get_or_create(message.from_user.id).id)
    await message.answer(f"{course[1]}: {course[0]}")


@router.message(F.text == 'Подписаться на обновления')
@router.message(F.text == 'Назад к выбору')
@router.message(Command('subscribe'))
async def subscribe_handler(message: types.Message):
    """
    Хандлер начала процесса подписки
    """
    user_mailing = Mailing.get_mailing_of_user(User.get_or_create(message.from_user.id).id)
    reply_text = 'Выберите интервал'
    reply_markup = interval_select_markup
    if user_mailing:
        reply_text += f'\nУ вас уже есть установленный интервал: {user_mailing.timing}.\nЧтобы заменить его введите новый интервал\nЧтобы отменить его нажмите "Отменить подписку"'
        reply_markup = interval_select_markup_has_mailing

    await message.answer(reply_text, reply_markup=reply_markup)


@router.message(F.text == 'Свой вариант')
async def custom_timer_variant(message: types.Message):
    """
    Описывает как добавить свой вариант
    """
    await message.answer('Введите интервал в формате \n"каждый 1 час 30 минут"\n"каждые 30 минут"\n', reply_markup=back_to_interval_selection)


@router.message(F.text.regexp(r'([кК]ажд)(.)*'))
async def subscribe_handler_next_step(message: types.Message):
    """
    Хандлер записи указанного интервала
    """
    mailing = Mailing.create_or_replace(user_id=message.from_user.id, message_text=message.text)

    if mailing[0]:
        await message.answer(mailing[1], reply_markup=main_menu_markup)
    else: 
        await message.answer('Не удалось установить таймер')


@router.message(F.text == 'Отменить подписку')
@router.message(Command('unsub', 'unsubscribe'))
async def unsubscribe_handler(message: types.Message):
    """
    Хандлер отписки
    """
    
    request = requests.get(f"http://localhost:8081/remove_timer/{message.from_user.id}")
    remove_stm = Mailing.remove_mailing(User.get_or_create(message.from_user.id).id)

    if '200' in request.text and remove_stm:
        await message.answer("Подписка успешно отменена", reply_markup=interval_select_markup)
    else:
        await message.answer('Не удалось отменить подписку')


@router.message(F.text == 'Просмотр истории')
@router.message(Command('history'))
async def course_history_handler(message: types.Message):
    """
    Хандлер отписки
    """
    logging.info(f'User {message.from_user.id} getting history')

    courses = Course.get_history(message.from_user.id)
    courses = [f'{datetime.strftime(c.date,"%Y.%m.%d %H:%M:%S")}: {c.valute_code} {c.value}' for c in courses]
    if len(courses) < 1:
        await message.answer("Вы не делали запросов")
        return 

    courses.reverse()
    courses = '\n'.join(courses)

    await message.answer(f"Ваши последние запросы:\n{courses}")