from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user_id
from common.database import get_db
from common.response import CustomResponse
from posts.service import PostService
from schemas import CommentCreate, CommentUpdate, PostCreate, PostUpdate

router = APIRouter(tags=["posts"])

PostId = Path(ge=1)
CommentId = Path(ge=1)
Cursor = Query(None, ge=1)
Size = Query(10, ge=1, le=50)


def get_service(db: Session = Depends(get_db)) -> PostService:
    return PostService(db)


@router.post("/posts")
def create_post(
    payload: PostCreate,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    return CustomResponse.success(
        data=service.create_post(user_id, payload),
        message="Post created",
        status_code=201,
    )


@router.get("/posts")
def get_feed(
    cursor: Optional[int] = Cursor,
    size: int = Size,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    result = service.get_feed(user_id, cursor, size)
    return CustomResponse.success(
        data=result["data"], extra_fields={"pagination": result["pagination"]}
    )


@router.get("/posts/{post_id}")
def get_post(
    post_id: int = PostId,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    return CustomResponse.success(data=service.get_post(user_id, post_id))


@router.patch("/posts/{post_id}")
def update_post(
    payload: PostUpdate,
    post_id: int = PostId,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    return CustomResponse.success(
        data=service.update_post(user_id, post_id, payload), message="Post updated"
    )


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int = PostId,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    return CustomResponse.success(
        data=service.delete_post(user_id, post_id), message="Post deleted"
    )


@router.post("/posts/{post_id}/react")
def toggle_post_reaction(
    post_id: int = PostId,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    return CustomResponse.success(data=service.toggle_post_reaction(user_id, post_id))


@router.get("/posts/{post_id}/likes")
def list_post_likers(
    post_id: int = PostId,
    cursor: Optional[int] = Cursor,
    size: int = Size,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    result = service.list_post_likers(user_id, post_id, cursor, size)
    return CustomResponse.success(
        data=result["data"], extra_fields={"pagination": result["pagination"]}
    )


@router.post("/posts/{post_id}/comments")
def create_comment(
    payload: CommentCreate,
    post_id: int = PostId,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    return CustomResponse.success(
        data=service.create_comment(user_id, post_id, payload),
        message="Comment created",
        status_code=201,
    )


@router.get("/posts/{post_id}/comments")
def list_comments(
    post_id: int = PostId,
    cursor: Optional[int] = Cursor,
    size: int = Size,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    result = service.list_comments(user_id, post_id, cursor, size)
    return CustomResponse.success(
        data=result["data"], extra_fields={"pagination": result["pagination"]}
    )


@router.get("/comments/{comment_id}/replies")
def list_replies(
    comment_id: int = CommentId,
    cursor: Optional[int] = Cursor,
    size: int = Size,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    result = service.list_replies(user_id, comment_id, cursor, size)
    return CustomResponse.success(
        data=result["data"], extra_fields={"pagination": result["pagination"]}
    )


@router.patch("/comments/{comment_id}")
def update_comment(
    payload: CommentUpdate,
    comment_id: int = CommentId,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    return CustomResponse.success(
        data=service.update_comment(user_id, comment_id, payload),
        message="Comment updated",
    )


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int = CommentId,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    return CustomResponse.success(
        data=service.delete_comment(user_id, comment_id), message="Comment deleted"
    )


@router.post("/comments/{comment_id}/react")
def toggle_comment_reaction(
    comment_id: int = CommentId,
    user_id: int = Depends(get_current_user_id),
    service: PostService = Depends(get_service),
):
    return CustomResponse.success(
        data=service.toggle_comment_reaction(user_id, comment_id)
    )
