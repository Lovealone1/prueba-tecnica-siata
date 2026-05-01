import redis.asyncio as redis
from app.core.settings import settings
from app.core.logger import logger

async def get_redis_client() -> redis.Redis | None:
    if not settings.REDIS_ENABLED:
        logger.warning("Redis is disabled by configuration")
        return None

    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        # Test connection
        await client.ping()
        logger.info(f"Redis is connected on {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect Redis on {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}: {str(e)}", exc_info=True)
        raise

async def close_redis_client(client: redis.Redis | None):
    if client:
        try:
            await client.aclose()
            logger.info("Redis client disconnected gracefully")
        except Exception as e:
            logger.error(f"Failed to gracefully disconnect Redis: {str(e)}")
