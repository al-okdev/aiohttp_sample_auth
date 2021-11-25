import json
from typing import Any, Callable

from aiohttp import web
from pydantic import ValidationError

from db.crud_ops import AlreadyExists
from db.models import User, AccessToken
from validators.models import VALIDATOR


def raise_exception(exception_class: type, body: dict):
    raise exception_class(text=json.dumps(body), content_type="application/json")


def validate(data: dict, pydantic_model: type(VALIDATOR)):
    try:
        return pydantic_model(**data).dict()
    except ValidationError as er:
        raise web.HTTPBadRequest(body=er.json())


def check_access(user: User, access_model, access: str):
    if not user.has_access(access_model, access):
        raise_exception(web.HTTPForbidden, {"error": "privilege required"})


async def get_object_or_404(model, object_id: int, session_maker):
    model_object = await model.get_by_id(object_id, session_maker)
    if not model_object:
        raise raise_exception(web.HTTPNotFound, {"error": "not found"})
    return model_object


async def get_object_by_field_or_404(model, field: str, value: Any, session_maker):

    return (await get_objects_by_field_or_404(model, field, value, session_maker))[0]


async def get_objects_by_field_or_404(model, field: str, value: Any, session_maker):
    model_objects = await model.get_by_field(field, value, session_maker)
    if not model_objects:
        raise_exception(web.HTTPNotFound, {"error": "not found"})
    return model_objects


async def paste_object(model, params: dict, session_maker):
    try:
        return await model.create(session_maker, **params)
    except AlreadyExists:
        raise_exception(web.HTTPConflict, {"error": "already exists"})


def check_token(handler: Callable) -> Callable:
    async def handler_with_check(request: web.Request, *args, **kwargs) -> web.Response:
        token = request.headers.get("token")
        token = await get_object_by_field_or_404(
            AccessToken, "token", token, request.app["async_session_maker"]
        )
        request.token = token
        request.user = User(token.user)
        return await handler(request, *args, **kwargs)

    return handler_with_check
