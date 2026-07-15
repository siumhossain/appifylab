from sqlalchemy.orm import Session

from auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from common.crud import get_crud
from common.response import CustomException
from schemas import UserCreate, UserLogin, UserOut

USER_FIELDS = ["id", "first_name", "last_name", "email", "created_at"]


class UserService:

    def __init__(self, db: Session):
        self.crud = get_crud(db)

    def register(self, payload: UserCreate) -> dict:
        if self.crud.exists("users", {"email": payload.email}):
            raise CustomException("", status_code=409)

        user = self.crud.create(
            "users",
            {
                "first_name": payload.first_name,
                "last_name": payload.last_name,
                "email": payload.email,
                "password_hash": hash_password(payload.password),
            },
            returning=USER_FIELDS,
        )
        return {"user": UserOut(**user).model_dump(), **self._token_pair(user["id"])}

    def login(self, payload: UserLogin) -> dict:
        user = self.crud.find_first("users", {"email": payload.email})
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise CustomException("Invalid email or password", status_code=401)
        if not user["is_active"]:
            raise CustomException("Account is deactivated", status_code=401)

        user_out = {k: user[k] for k in USER_FIELDS}
        return {"user": UserOut(**user_out).model_dump(), **self._token_pair(user["id"])}

    def refresh(self, refresh_token: str) -> dict:
        user_id = decode_token(refresh_token, "refresh")
        if not self.crud.exists("users", {"id": user_id, "is_active": True}):
            raise CustomException("User not found", status_code=401)
        return self._token_pair(user_id)

    def get_me(self, user_id: int) -> dict:
        user = self.crud.find_first(
            "users", {"id": user_id, "is_active": True}, fields=USER_FIELDS
        )
        if not user:
            raise CustomException("User not found", status_code=404)
        return UserOut(**user).model_dump()

    @staticmethod
    def _token_pair(user_id: int) -> dict:
        return {
            "access_token": create_access_token(user_id),
            "refresh_token": create_refresh_token(user_id),
            # "token_type": "bearer",
        }
