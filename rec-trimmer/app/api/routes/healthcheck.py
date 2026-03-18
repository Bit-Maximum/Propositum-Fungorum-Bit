from fastapi import APIRouter, status


router: APIRouter = APIRouter(
    prefix="/trimmer/healthcheck",
    tags=["healthcheck",]
)


@router.get(path="/", status_code=status.HTTP_200_OK,)
async def get_healthcheck():
    return {
        "status": "ok"
    }
