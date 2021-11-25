import secrets
import time

import bcrypt

import config
import db.db_models
from db.crud_ops import BaseCrudModel


class Right(BaseCrudModel):
    access_alias = db.db_models.AccessObject('right')
    orm_class = db.db_models.Right


class Group(BaseCrudModel):
    access_alias = db.db_models.AccessObject('group')
    orm_class = db.db_models.Group


class User(BaseCrudModel):
    access_alias = db.db_models.AccessObject('user')
    orm_class = db.db_models.User
    exclude_fields = {'password'}

    @classmethod
    async def create(cls, async_session_maker, **kwargs):
        kwargs['password'] = bcrypt.hashpw(kwargs['password'].encode(), bcrypt.gensalt()).decode()
        return await super().create(async_session_maker, **kwargs)

    def check_password(self, password: str):
        return bcrypt.checkpw(password.encode(), self.password.encode())

    @property
    def privileges(self):
        return set((right.object, right.access, right.scope) for right in self.group.rights)

    def is_owner(self, crud_object):

        if isinstance(crud_object, self.__class__):
            return crud_object.id == self.id

        if hasattr(crud_object, 'owner_id'):
            return self.id == crud_object.owner_id

        return False

    def has_access(self, crud_object, access: str):
        possible_scopes = (
            db.db_models.AccessScope('self'),
            db.db_models.AccessScope('all')
        ) if self.is_owner(crud_object) else (
            db.db_models.AccessScope('all'),
        )
        privileges = self.privileges
        access = db.db_models.AccessRight(access)
        for scope in possible_scopes:
            if (crud_object.access_alias, access, scope) in privileges:
                return True


class AccessToken(BaseCrudModel):
    access_alias = 'access_token'
    orm_class = db.db_models.AccessToken

    exclude_fields = {'user'}

    @property
    def is_expired(self):
        return time.time() - self.creation_time.timestamp() > config.TOKEN_TTL

    @classmethod
    async def get_by_token(cls, token: str, async_session_maker):
        tokens = await cls.get_by_field('token', token, async_session_maker)
        return tokens[0] if tokens else None

    @classmethod
    async def create(cls, async_session_maker, user: User):
        token = secrets.token_urlsafe(config.TOKEN_LENGTH)
        return await super().create(async_session_maker, user=user, token=token)


class Post(BaseCrudModel):
    access_alias = 'post'
    orm_class = db.db_models.Post
