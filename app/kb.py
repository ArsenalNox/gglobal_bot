"""
Лейаут клавиатур
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

#Клавиатура главного меню, меню при старте бота
main_menu_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
        KeyboardButton(text='Получить курс USD'),
        KeyboardButton(text='Подписаться на обновления'),
        KeyboardButton(text='Просмотр истории'),
        ]
    ],
    resize_keyboard=True
)

#TODO: Релизовать билдер клавы на случай если есть интервал
#Клавиатура выбора интервала
interval_select_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
        KeyboardButton(text='Каждые 30 минут'),
        KeyboardButton(text='Каждый 1 час'),
        KeyboardButton(text='Каждый 2 часа 30 минут'),
        KeyboardButton(text='Свой вариант'),
        KeyboardButton(text='Назад в меню'),
        ]
    ],
    resize_keyboard=True
)


#Клавиатура выбора интервала если есть интервал
interval_select_markup_has_mailing = ReplyKeyboardMarkup(
    keyboard=[
        [
        KeyboardButton(text='Каждые 30 минут'),
        KeyboardButton(text='Каждый 1 час'),
        KeyboardButton(text='Каждый 2 часа 30 минут'),
        KeyboardButton(text='Свой вариант'),
        KeyboardButton(text='Отменить подписку'),
        ]
    ],
    resize_keyboard=True
)


back_to_interval_selection = ReplyKeyboardMarkup(
    keyboard=[
        [
        KeyboardButton(text='Назад к выбору'),
        KeyboardButton(text='Назад в меню'),
        ]
    ],
    resize_keyboard=True
)