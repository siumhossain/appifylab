from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    # token_type: Literal["bearer"] = "bearer"


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime


class PostCreate(BaseModel):
    content: str = Field(default="", max_length=10000)
    image_urls: List[str] = Field(default_factory=list, max_length=10)
    privacy: Literal["public", "private"] = "public"

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        return v.strip()

    @field_validator("image_urls")
    @classmethod
    def validate_url_lengths(cls, v: List[str]) -> List[str]:
        if any(len(u) > 1024 for u in v):
            raise ValueError("image_urls entries must be at most 1024 characters")
        return v

    @model_validator(mode="after")
    def require_content_or_image(self):
        if not self.content and not self.image_urls:
            raise ValueError("Post must have content or an image")
        return self


class PostUpdate(BaseModel):
    content: Optional[str] = Field(None, max_length=10000)
    image_urls: Optional[List[str]] = Field(None, max_length=10)
    privacy: Optional[Literal["public", "private"]] = None

    @field_validator("image_urls")
    @classmethod
    def validate_url_lengths(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and any(len(u) > 1024 for u in v):
            raise ValueError("image_urls entries must be at most 1024 characters")
        return v

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v is not None else v


class PostOut(BaseModel):
    id: int
    user_id: int
    content: str
    image_urls: List[str]
    privacy: Literal["public", "private"]
    reaction_count: int
    comment_count: int
    created_at: datetime


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    parent_comment_id: Optional[int] = Field(None, ge=1)

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("content cannot be blank")
        return v


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("content cannot be blank")
        return v


class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    parent_comment_id: Optional[int]
    content: str
    reaction_count: int
    reply_count: int
    created_at: datetime
