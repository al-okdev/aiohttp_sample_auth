import enum

from sqlalchemy import (
    Table,
    DateTime,
    Column,
    String,
    Integer,
    Enum,
    ForeignKey,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class AccessObject(str, enum.Enum):
    user: str = "user"
    group: str = "group"
    right: str = "right"
    post: str = "post"


class AccessRight(str, enum.Enum):
    read: str = "read"
    write: str = "write"


class AccessScope(str, enum.Enum):
    self: str = "self"
    all: str = "all"


group_rights = Table(
    "group_rights",
    Base.metadata,
    Column("right_id", ForeignKey("right.id"), primary_key=True),
    Column("group_id", ForeignKey("group.id"), primary_key=True),
)


class Right(Base):

    __tablename__ = "right"
    __table_args__ = (
        UniqueConstraint("object", "access", "scope", name="_customer_location_uc"),
    )

    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    object = Column(Enum(AccessObject), nullable=False)
    access = Column(Enum(AccessRight), nullable=False)
    scope = Column(Enum(AccessScope), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.object} {self.access}"


class Group(Base):

    __tablename__ = "group"

    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(256), nullable=False, unique=True)
    rights = relationship("Right", secondary=group_rights, lazy="joined")


class User(Base):

    __tablename__ = "user"

    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    email = Column(String(256), unique=True, index=True)
    password = Column(String(128), nullable=False)
    group_id = Column(Integer, ForeignKey("group.id"), nullable=True)
    group = relationship("Group", lazy="joined")


class AccessToken(Base):

    __tablename__ = "access_token"

    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", lazy="joined")
    creation_time = Column(DateTime(timezone=True), server_default=func.now())


class Post(Base):

    __tablename__ = "post"

    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    owner = relationship("User", lazy="joined")
    title = Column(String(128), nullable=False)
    text = Column(String, nullable=False)
