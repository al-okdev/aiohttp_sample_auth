import re
import typing

import pydantic

from db.db_models import AccessRight, AccessObject, AccessScope

STRONG_PASSWORD = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$")
CORRECT_ID = re.compile(r"\d+")


class UserCreate(pydantic.BaseModel):

    email: pydantic.EmailStr
    password: str
    group_id: int

    @pydantic.validator('password')
    def password_strong(value: str):
        if not STRONG_PASSWORD.match(value):
            raise ValueError('password is to easy')
        return value


class Login(pydantic.BaseModel):
    email: pydantic.EmailStr
    password: str


class ObjectId(pydantic.BaseModel):
    id: str

    @pydantic.validator('id')
    def id_validator(value: str):
        if CORRECT_ID.match(value):
            return int(value)


class RightCreate(pydantic.BaseModel):
    object: AccessObject
    access: AccessRight
    scope: AccessScope


class PostCreate(pydantic.BaseModel):
    title: str
    text: str


class PostUpdate(pydantic.BaseModel):
    title: typing.Optional[str] = None
    text: typing.Optional[str] = None

    @pydantic.root_validator
    def any(cls, values):
        values = {key: value for key, value in values.items() if value is not None}
        if not values:
            raise ValueError('At least one field must be defined')
        return values


VALIDATOR = typing.Union[UserCreate, Login, ObjectId, RightCreate]
