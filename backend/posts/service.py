
from typing import Optional

from sqlalchemy.orm import Session

from common.config import get_settings
from common.response import CustomException
from posts.repository import PostRepository
from schemas import CommentCreate, CommentUpdate, PostCreate, PostUpdate

settings = get_settings()


class PostService:

    def __init__(self, db: Session):
        self.repo = PostRepository(db)

    @staticmethod
    def _validate_image_urls(urls: list[str]) -> None:
        prefix = f"{settings.R2_PUBLIC_URL}/"
        if any(not url.startswith(prefix) for url in urls):
            raise CustomException(
                "image_urls must be files uploaded via /upload", status_code=422
            )

    def _get_post(self, post_id: int) -> dict:
        post = self.repo.find_post(post_id)
        if not post:
            raise CustomException("Post not found", status_code=404)
        return post

    def _get_visible_post(self, post_id: int, user_id: int) -> dict:
        post = self._get_post(post_id)
        if post["privacy"] == "private" and post["user_id"] != user_id:
            raise CustomException("Post not found", status_code=404)
        return post

    def _get_comment(self, comment_id: int) -> dict:
        comment = self.repo.find_comment(comment_id)
        if not comment:
            raise CustomException("Comment not found", status_code=404)
        return comment

    def create_post(self, user_id: int, payload: PostCreate) -> dict:
        self._validate_image_urls(payload.image_urls)
        return self.repo.create_post(
            {
                "user_id": user_id,
                "content": payload.content,
                "image_urls": payload.image_urls,
                "privacy": payload.privacy,
            }
        )

    def get_feed(self, user_id: int, cursor: Optional[int], size: int) -> dict:
        return self.repo.feed_page(user_id, cursor, size)

    def get_post(self, user_id: int, post_id: int) -> dict:
        post = self.repo.find_post_with_author(post_id, user_id)
        if not post or (post["privacy"] == "private" and post["user_id"] != user_id):
            raise CustomException("Post not found", status_code=404)
        return post

    def update_post(self, user_id: int, post_id: int, payload: PostUpdate) -> dict:
        post = self._get_post(post_id)
        if post["user_id"] != user_id:
            raise CustomException("Unauthorized", status_code=403)

        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise CustomException("Nothing to update", status_code=422)
        if "image_urls" in changes:
            changes["image_urls"] = changes["image_urls"] or []
            self._validate_image_urls(changes["image_urls"])

        new_content = changes.get("content", post["content"])
        new_images = changes.get("image_urls", post["image_urls"])
        if not new_content and not new_images:
            raise CustomException("Post must have content or an image", status_code=422)

        return self.repo.update_post(post_id, changes)

    def delete_post(self, user_id: int, post_id: int) -> dict:
        post = self._get_post(post_id)
        if post["user_id"] != user_id:
            raise CustomException("Unauthorized", status_code=403)
    
        self.repo.delete_post(post_id)
        return {"deleted": True}

    def toggle_post_reaction(self, user_id: int, post_id: int) -> dict:
        self._get_visible_post(post_id, user_id)
        reacted = self.repo.toggle_reaction("post_reactions", "post_id", post_id, user_id)
        return {"reacted": reacted}

    def list_post_likers(
        self, user_id: int, post_id: int, cursor: Optional[int], size: int
    ) -> dict:
        self._get_visible_post(post_id, user_id)
        return self.repo.post_likers_page(post_id, cursor, size)

    def create_comment(self, user_id: int, post_id: int, payload: CommentCreate) -> dict:
        self._get_visible_post(post_id, user_id)
        if payload.parent_comment_id is not None:
            parent = self._get_comment(payload.parent_comment_id)
            if parent["post_id"] != post_id:
                raise CustomException(
                    "Parent comment belongs to another post", status_code=422
                )
            if parent["parent_comment_id"] is not None:
                raise CustomException(
                    "Replies can only be one level deep", status_code=422
                )
        return self.repo.create_comment(
            {
                "post_id": post_id,
                "user_id": user_id,
                "parent_comment_id": payload.parent_comment_id,
                "content": payload.content,
            }
        )

    def list_comments(
        self, user_id: int, post_id: int, cursor: Optional[int], size: int
    ) -> dict:
        self._get_visible_post(post_id, user_id)
        return self.repo.comments_page(post_id, user_id, cursor, size)

    def list_replies(
        self, user_id: int, comment_id: int, cursor: Optional[int], size: int
    ) -> dict:
        comment = self._get_comment(comment_id)
        self._get_visible_post(comment["post_id"], user_id)
        return self.repo.replies_page(comment_id, user_id, cursor, size)

    def update_comment(
        self, user_id: int, comment_id: int, payload: CommentUpdate
    ) -> dict:
        comment = self._get_comment(comment_id)
        if comment["user_id"] != user_id:
            raise CustomException(
                "You can only edit your own comments", status_code=403
            )
        return self.repo.update_comment(comment_id, payload.content)

    def delete_comment(self, user_id: int, comment_id: int) -> dict:
        comment = self._get_comment(comment_id)
        if comment["user_id"] != user_id:
            post = self._get_post(comment["post_id"])
            if post["user_id"] != user_id:
                raise CustomException(
                    "Unauthorized",
                    status_code=403,
                )
        self.repo.delete_comment(comment_id)
        return {"deleted": True}

    def toggle_comment_reaction(self, user_id: int, comment_id: int) -> dict:
        comment = self._get_comment(comment_id)
        self._get_visible_post(comment["post_id"], user_id)
        reacted = self.repo.toggle_reaction(
            "comment_reactions", "comment_id", comment_id, user_id
        )
        return {"reacted": reacted}
