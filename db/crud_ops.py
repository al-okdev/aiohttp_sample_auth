import abc
from contextlib import asynccontextmanager

import sqlalchemy
from sqlalchemy.future import select
from typing import Iterable, Any
from sqlalchemy.exc import IntegrityError


import db.models


class AlreadyExists(Exception):
    pass


@asynccontextmanager
async def get_session(async_session_maker):
    async with async_session_maker() as session:
        async with session.begin():
            yield session


async def get_by_id(orm_class, object_id: int, async_session_maker):
    async with get_session(async_session_maker) as session:
        return await session.get(orm_class, object_id)


async def get_by_field(orm_class, field: str, value: Any, async_session_maker):
    query = select(orm_class).where(getattr(orm_class, field) == value)

    async with get_session(async_session_maker) as session:
        result = await session.execute(query)
        return list(result.unique().scalars())


async def insert(orm_object, async_session_maker):
    async with get_session(async_session_maker) as session:
        session.add(orm_object)
        try:
            await session.commit()
        except IntegrityError as er:

            raise AlreadyExists

        return orm_object


async def insert_many(orm_objects: Iterable, async_session_maker):
    async with get_session(async_session_maker) as session:
        session.add_all(orm_objects)
        await session.commit()
        return orm_objects


async def update(orm_object, patch: dict, async_session_maker):

    async with get_session(async_session_maker) as session:
        for key, value in patch.items():
            setattr(orm_object, key, value)
        statement = sqlalchemy.update(orm_object.orm_class).values(**patch)
        statement.execution_options(synchronize_session="fetch")
        await session.execute(statement)
        await session.commit()
    return orm_object


class BaseCrudModel(abc.ABC):
    orm_class = None
    access_alias = None
    exclude_fields = set()

    def __init__(self, orm_object=None, **kwargs):
        self.orm_object = orm_object or self.orm_class(**kwargs)

    @classmethod
    async def create(cls, async_session_maker, **kwargs):
        return cls(await insert(cls.orm_class(**kwargs), async_session_maker))

    @classmethod
    async def create_many(cls, async_session_maker, objects_data: Iterable):
        orm_objects = [cls.orm_class(**object_data) for object_data in objects_data]
        return await insert_many(orm_objects, async_session_maker)

    @classmethod
    async def get_by_id(cls, object_id: int, async_session_maker):
        orm_object = await get_by_id(cls.orm_class, object_id, async_session_maker)
        if orm_object:
            return cls(orm_object)

    @classmethod
    async def get_by_field(cls, field: str, value: Any, async_session_maker):
        return [
            cls(obj)
            for obj in await get_by_field(
                cls.orm_class, field, value, async_session_maker
            )
        ]

    async def patch(self, patch_data: dict, async_session_maker):
        return await update(self, patch_data, async_session_maker)

    def __getattr__(self, attr: str):
        return getattr(self.orm_object, attr)

    def __setattr__(self, key: str, value: Any):
        if key == "orm_object":
            return super().__setattr__(key, value)
        else:
            setattr(self.orm_object, key, value)

    @property
    def dict(self):
        return {
            key: value
            for key, value in self.orm_object.__dict__.items()
            if not callable(value)
            and not key.startswith("_")
            and key not in self.exclude_fields
        }
