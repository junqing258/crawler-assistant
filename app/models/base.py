"""数据模型基类"""

import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.mysql import CHAR as MySQLCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase


# MySQL兼容的UUID类型
class GUID(TypeDecorator):
    """MySQL兼容的UUID类型"""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            return dialect.type_descriptor(MySQLCHAR(36))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class Base(DeclarativeBase):
    """数据模型基类"""
    pass


class BaseModel(Base):
    """带有通用字段的基础模型"""
    
    __abstract__ = True
    
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        comment="主键ID"
    )
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"

