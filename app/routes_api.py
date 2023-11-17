import json
import logging 

from aiohttp import web

from bot import bot 
from models import User, Course

router_api = web.RouteTableDef()


@router_api.get('/api')
async def api_index(request):
    return web.Response(text='Hello')


@router_api.get('/api/users')
async def get_user(request):
    users = User.get_all()

    users = [u.telegram_id for u in users]

    return web.json_response(users)


@router_api.get('/api/trigger_reminder/{user_id}')
async def trigger_reminder(request):
    """
    Отправка курса по таймеру от сервера с таймерами
    """
    user_id = request.match_info.get('user_id', "")
    logging.debug(f"SEND TO USER {user_id}")
    
    course = Course.get_current_rate(User.get_or_create(user_id).id)

    await bot.send_message(user_id, f"{course[1]}: {course[0]}")

    return web.Response(text='Sent')