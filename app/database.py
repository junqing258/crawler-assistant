"""数据库配置和连接管理"""

import asyncio
from typing import AsyncGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from app.config import settings
from app.models.base import Base
import logging

logger = logging.getLogger(__name__)

# 同步数据库引擎
engine = create_engine(
    settings.database_url.replace("+aiomysql", "+pymysql"),
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 异步数据库引擎
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Redis连接
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
async_redis_client = AsyncRedis.from_url(settings.redis_url, decode_responses=True)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.async_engine = async_engine
    
    def create_tables(self) -> None:
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise
    
    async def create_tables_async(self) -> None:
        """异步创建所有表"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建成功 (异步)")
        except Exception as e:
            logger.error(f"数据库表创建失败 (异步): {e}")
            raise
    
    def drop_tables(self) -> None:
        """删除所有表"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"数据库表删除失败: {e}")
            raise
    
    async def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False
    
    async def check_redis_connection(self) -> bool:
        """检查Redis连接"""
        try:
            await async_redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis连接检查失败: {e}")
            return False


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 依赖注入函数
def get_db() -> Session:
    """获取数据库会话 (同步)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话 (异步)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_redis() -> Redis:
    """获取Redis客户端 (同步)"""
    return redis_client


async def get_async_redis() -> AsyncRedis:
    """获取Redis客户端 (异步)"""
    return async_redis_client


class DatabaseService:
    """数据库服务基类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def commit(self) -> None:
        """提交事务"""
        await self.db.commit()
    
    async def rollback(self) -> None:
        """回滚事务"""
        await self.db.rollback()
    
    async def refresh(self, instance) -> None:
        """刷新实例"""
        await self.db.refresh(instance)
    
    async def add(self, instance) -> None:
        """添加实例"""
        self.db.add(instance)
    
    async def delete(self, instance) -> None:
        """删除实例"""
        await self.db.delete(instance)
    
    async def flush(self) -> None:
        """刷新到数据库"""
        await self.db.flush()


class RedisService:
    """Redis服务类"""
    
    def __init__(self):
        self.redis = async_redis_client
    
    async def set(self, key: str, value: str, expire: int = None) -> bool:
        """设置键值"""
        try:
            return await self.redis.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Redis设置失败: {e}")
            return False
    
    async def get(self, key: str) -> str:
        """获取值"""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis获取失败: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """删除键"""
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis存在检查失败: {e}")
            return False
    
    async def incr(self, key: str) -> int:
        """递增计数器"""
        try:
            return await self.redis.incr(key)
        except Exception as e:
            logger.error(f"Redis递增失败: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis设置过期时间失败: {e}")
            return False
    
    async def hset(self, name: str, mapping: dict) -> int:
        """设置哈希"""
        try:
            return await self.redis.hset(name, mapping=mapping)
        except Exception as e:
            logger.error(f"Redis哈希设置失败: {e}")
            return 0
    
    async def hget(self, name: str, key: str) -> str:
        """获取哈希值"""
        try:
            return await self.redis.hget(name, key)
        except Exception as e:
            logger.error(f"Redis哈希获取失败: {e}")
            return None
    
    async def hgetall(self, name: str) -> dict:
        """获取所有哈希值"""
        try:
            return await self.redis.hgetall(name)
        except Exception as e:
            logger.error(f"Redis哈希获取全部失败: {e}")
            return {}


# 全局服务实例
redis_service = RedisService()


async def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 检查数据库连接
        if not await db_manager.check_connection():
            raise Exception("数据库连接失败")
        
        # 检查Redis连接
        if not await db_manager.check_redis_connection():
            logger.warning("Redis连接失败，某些功能可能不可用")
        
        # 创建表
        await db_manager.create_tables_async()
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def close_database():
    """关闭数据库连接"""
    try:
        await async_engine.dispose()
        await async_redis_client.close()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


# 启动时初始化
async def startup_database():
    """应用启动时的数据库初始化"""
    await init_database()


# 关闭时清理
async def shutdown_database():
    """应用关闭时的数据库清理"""
    await close_database()

