from sqlalchemy import (Column, String, Integer, ForeignKey, DateTime,
                        func, DateTime, UniqueConstraint, Text)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    description = Column(String, unique=False, nullable=True)
    token = Column(String, nullable=True, unique=True)
    avatar_path = Column(String, nullable=True)

    created_groups = relationship("Group", back_populates="creator", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="author", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMember", back_populates="user")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    avatar_path = Column(String, nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    creator = relationship("User", back_populates="created_groups")
    messages = relationship("Message", back_populates="group", cascade="all, delete-orphan")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")



class GroupMember(Base):
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default="member")
    joined_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_member"),)
    
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)

    group = relationship("Group", back_populates="messages")
    author = relationship("User", back_populates="messages")