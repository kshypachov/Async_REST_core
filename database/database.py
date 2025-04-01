# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config.config import get_database_url
from config.config import get_logger

# створюється екземпляр класу logger
logger = get_logger(__name__)

try:
    DATABASE_URL = get_database_url()
except ValueError as e:
    logger.critical(f"Failed to load configuration in database module: {e}")
    exit(1)


engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Функция для получения сессии
async def get_db():
    async with SessionLocal() as session:
        yield session