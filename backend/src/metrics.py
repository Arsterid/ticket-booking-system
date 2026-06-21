import secrets
from fastapi import FastAPI, HTTPException, Depends, status, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.core.settings import settings

security = HTTPBearer()


def verify_metrics_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not secrets.compare_digest(credentials.credentials, settings.metrics_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def init_metrics(app: FastAPI) -> None:
    Instrumentator().instrument(app=app)

    @app.get("/metrics", dependencies=[Depends(verify_metrics_token)], tags=["Monitoring"])
    async def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
