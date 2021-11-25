from config import DB
from db.sessions import get_async_session
from db.models import Group, Right, User
import asyncio


admin_rights_data = [
    {'object': 'right', 'access': 'write', 'scope': 'all'},
    {'object': 'right', 'access': 'read', 'scope': 'all'},
    {'object': 'group', 'access': 'write', 'scope': 'all'},
    {'object': 'group', 'access': 'read', 'scope': 'all'},
    {'object': 'user', 'access': 'write', 'scope': 'all'},
    {'object': 'user', 'access': 'read', 'scope': 'all'},
    {'object': 'post', 'access': 'write', 'scope': 'all'},
    {'object': 'post', 'access': 'read', 'scope': 'all'},
]

user_rights_data = [
    {'object': 'user', 'access': 'write', 'scope': 'self'},
    {'object': 'user', 'access': 'read', 'scope': 'self'},
    {'object': 'post', 'access': 'write', 'scope': 'self'},
]


async def hook_db():
    async with get_async_session(DB, True, True) as async_session_maker:

        admin_rights = await Right.create_many(async_session_maker, admin_rights_data)
        user_rights = await Right.create_many(async_session_maker, user_rights_data)
        admin_group = await Group.create(
            async_session_maker,
            name='admin',
            rights=admin_rights
        )
        user_group = await Group.create(
            async_session_maker,
            name='user',
            rights=[admin_rights[-1], *user_rights]
        )
        await User.create(async_session_maker, password='1234', email='admin@admin.com', group=admin_group)
        await User.create(async_session_maker, password='1234', email='user@user.com', group=user_group)


if __name__ == '__main__':
    asyncio.run(hook_db())