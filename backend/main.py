import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from auth.security import decode_token
from common.database import check_database_connection, dispose_engine
from common.migrate import run_migrations
from common.rate_limiter import get_client_ip, rate_limiter
from common.redis_client import check_redis_connection
from common.r2 import router as upload_router
from common.response import CustomException, CustomResponse
from posts.router import router as posts_router
from users.router import router as users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not check_database_connection():
        raise RuntimeError("Database connection failed")
    if not check_redis_connection():
        raise RuntimeError("Redis connection failed")
    run_migrations()
    logger.info("Startup complete: database, redis, migrations OK")
    yield
    dispose_engine()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "http://103.23.95.103:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _rate_limit_identity(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        try:
            return f"user:{decode_token(auth[7:], 'access')}"
        except CustomException:
            pass
    return f"ip:{get_client_ip(request)}"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    allowed, retry_after = rate_limiter.check(
        _rate_limit_identity(request), request.method
    )
    if not allowed:
        response = CustomResponse.error(message="Too many requests", status_code=429)

        return response
    return await call_next(request)
app.include_router(users_router)
app.include_router(posts_router)
app.include_router(upload_router)


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return CustomResponse.error(
        message=exc.message,
        status_code=exc.status_code,
        extra_fields=exc.extra_fields or {},
    )


@app.get("/health")
async def health():
    return {
        "database": check_database_connection(),
        "redis": check_redis_connection(),
    }
