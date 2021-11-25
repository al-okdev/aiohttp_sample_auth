import os

DB = os.getenv("DB", "postgresql+asyncpg://app:secret@database:5432/app")
TOKEN_TTL = 86400
TOKEN_LENGTH = 256
