from apis.routes.backend import login as route_backend_loging
from apis.routes.backend import user as route_backend_user
from apis.routes.frontend import login as route_frontend_loging
from apis.routes.frontend import nlp_topic_builder
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(
    route_frontend_loging.router, prefix="", tags=["login-frontend"]
)
api_router.include_router(
    nlp_topic_builder.router, prefix="", tags=["nlp-topic-builder"]
)
api_router.include_router(
    route_backend_user.router, prefix="/api/user", tags=["user-backend"]
)
api_router.include_router(
    route_backend_loging.router, prefix="/api/login", tags=["login-backend"]
)
