from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.security import decode_token
from common.response import CustomException

bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> int:
    if credentials is None:
        raise CustomException("Not authenticated", status_code=401)
    return decode_token(credentials.credentials, "access")
