from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user_id
from common.database import get_db
from common.response import CustomResponse
from schemas import RefreshIn, UserCreate, UserLogin
from users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.post("/register")
def register(payload: UserCreate, service: UserService = Depends(get_service)):
    return CustomResponse.success(
        data=service.register(payload), message="User registered", status_code=201
    )


@router.post("/login")
def login(payload: UserLogin, service: UserService = Depends(get_service)):
    return CustomResponse.success(data=service.login(payload), message="Login successful")


@router.post("/refresh")
def refresh(payload: RefreshIn, service: UserService = Depends(get_service)):
    return CustomResponse.success(
        data=service.refresh(payload.refresh_token), message="Token refreshed"
    )


@router.get("/me")
def me(
    user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_service),
):
    return CustomResponse.success(data=service.get_me(user_id))
