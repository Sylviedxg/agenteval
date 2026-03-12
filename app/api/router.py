from fastapi import APIRouter

from app.api.v1.products import router as products_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.eval_plans import router as eval_plans_router
from app.api.v1.badcases import router as badcases_router
from app.api.v1.traces import router as traces_router
from app.api.v1.changelogs import router as changelogs_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.mock import router as mock_router

api_router = APIRouter()

api_router.include_router(products_router)
api_router.include_router(experiments_router)
api_router.include_router(datasets_router)
api_router.include_router(eval_plans_router)
api_router.include_router(badcases_router)
api_router.include_router(traces_router)
api_router.include_router(changelogs_router)
api_router.include_router(dashboard_router)
api_router.include_router(mock_router)


@api_router.get("/ping")
async def ping():
    return {"message": "pong"}
