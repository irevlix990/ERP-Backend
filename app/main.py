from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from Backend.app.core import auth
from app.routers import workspace, project

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5/minute"]
)

app = FastAPI(title="ERP Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def inject_rate_limit(request: Request, call_next):
    # Terapkan rate limit hanya ke endpoint /auth/*
    if "/auth" in request.url.path:
        # Contoh: Batasi 2 request per 10 detik untuk enpoint auth
        limiter.limit("2/10second")(call_next)
    return await limiter.limit_request(request, call_next)

app.include_router(auth.router)
app.include_router(workspace.router)
app.include_router(project.router)