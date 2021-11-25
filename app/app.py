from aiohttp import web

import config
import db.models
from db.sessions import get_async_session
from app.rest import (validate, get_object_by_field_or_404, get_object_or_404, check_token, check_access, paste_object,
                      raise_exception)
from validators.models import Login, UserCreate, ObjectId, RightCreate, PostCreate


async def database_context(app: web.Application):
    async with get_async_session(config.DB) as async_session_maker:
        app['async_session_maker'] = async_session_maker
        yield


def get_session_maker(request: web.Request):
    return request.app['async_session_maker']


async def login(request: web.Request):
    login_data = validate(await request.json(), Login)
    user = await get_object_by_field_or_404(db.models.User, 'email', login_data['email'], get_session_maker(request))
    if not user.check_password(login_data['password']):
        raise_exception(web.HTTPUnauthorized, {'error': 'wrong password'})
    new_token = await db.models.AccessToken.create(get_session_maker(request), user)
    return web.json_response(new_token.dict)


@check_token
async def create_user(request: web.Request):
    user_data = validate(await request.json(), UserCreate)
    check_access(request.user, db.models.User, 'write')
    new_user = await paste_object(db.models.User, user_data, get_session_maker(request))
    return web.json_response(new_user.dict)


@check_token
async def get_right(request: web.Request):
    right_id = validate(request.match_info, ObjectId)['id']
    right = await get_object_or_404(db.models.Right, right_id, get_session_maker(request))
    check_access(request.user, right, 'read')
    return web.json_response(right.dict)


@check_token
async def create_right(request: web.Request):
    right_data = validate(await request.json(), RightCreate)
    check_access(request.user, db.models.Right, 'write')
    new_right = await paste_object(db.models.Right, right_data, get_session_maker(request))
    return web.json_response(new_right.dict)


async def get_post(request: web.Request):
    post_id = validate(request.match_info, ObjectId)['id']
    post = await get_object_or_404(db.models.Post, post_id, get_session_maker(request))
    return web.json_response(post.dict)


@check_token
async def create_post(request: web.Request):
    post_data = validate(await request.json(), PostCreate)
    post_data['owner_id'] = request.user.id
    new_post = db.models.Post(**post_data)
    check_access(request.user, new_post, 'write')
    new_post = await paste_object(db.models.Post, post_data, get_session_maker(request))
    return web.json_response(new_post.dict)


@check_token
async def update_post(request: web.Request):
    post_data = validate(await request.json(), PostCreate)


async def check_health(request: web.Request):
    return web.json_response({'status': 'OK'})


async def get_app() -> web.Application:
    app = web.Application()
    app.cleanup_ctx.append(database_context)
    app.router.add_routes([
        web.get('/health', check_health),
        web.post('/login', login),
        web.post('/user', create_user),
        web.get('/right/{id:\d+}', get_right),
        web.post('/right', create_right),
        web.get('/post/{id:\d+}', get_post),
        web.post('/post', create_post),
        web.patch('/post', create_post),
    ])
    return app

