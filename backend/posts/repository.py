from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from common.crud import get_crud

POST_SELECT = """
    SELECT p.id, p.user_id, p.content, p.image_urls, p.privacy,
           p.reaction_count, p.comment_count, p.created_at,
           u.first_name, u.last_name,
           (p.user_id = :me) AS is_owner,
           EXISTS(SELECT 1 FROM post_reactions r
                  WHERE r.post_id = p.id AND r.user_id = :me) AS reacted
    FROM posts p
    JOIN users u ON u.id = p.user_id
"""

COMMENT_SELECT = """
    SELECT c.id, c.post_id, c.user_id, c.parent_comment_id, c.content,
           c.reaction_count, c.reply_count, c.created_at,
           u.first_name, u.last_name,
           (c.user_id = :me) AS is_owner,
           EXISTS(SELECT 1 FROM comment_reactions r
                  WHERE r.comment_id = c.id AND r.user_id = :me) AS reacted
    FROM comments c
    JOIN users u ON u.id = c.user_id
"""

POST_LIKERS_SELECT = """
    SELECT u.id, u.first_name, u.last_name
    FROM post_reactions r
    JOIN users u ON u.id = r.user_id
    WHERE r.post_id = :post_id AND u.is_active
"""

POST_ACTIVE = " p.is_active AND u.is_active"
COMMENT_ACTIVE = " c.is_active AND u.is_active"

FEED_WHERE = f" WHERE (p.privacy = 'public' OR p.user_id = :me) AND{POST_ACTIVE}"
POST_BY_ID_WHERE = f" WHERE p.id = :post_id AND{POST_ACTIVE}"
TOP_LEVEL_COMMENTS_WHERE = (
    f" WHERE c.post_id = :post_id AND c.parent_comment_id IS NULL AND{COMMENT_ACTIVE}"
)
REPLIES_WHERE = f" WHERE c.parent_comment_id = :parent_id AND{COMMENT_ACTIVE}"

REACT_INSERT = """
    INSERT INTO {table} ({target_col}, user_id)
    VALUES (:target_id, :user_id)
    ON CONFLICT DO NOTHING
    RETURNING user_id
"""


class PostRepository:

    def __init__(self, db: Session):
        self.crud = get_crud(db)

    def _page(self, query: str, params: Dict[str, Any], cursor: Optional[int],
              size: int, id_field: str = "p.id", descending: bool = True) -> dict:
        return self.crud.execute_query(query, params, {
            "paginate": True,
            "size": size,
            "cursor": cursor,
            "cursor_field": id_field,
            "order_by": f"{id_field} {'DESC' if descending else 'ASC'}",
        })

    def find_post(self, post_id: int) -> Optional[dict]:
        return self.crud.find_first("posts", {"id": post_id, "is_active": True})

    def find_post_with_author(self, post_id: int, user_id: int) -> Optional[dict]:
        return self.crud.execute_query(
            POST_SELECT + POST_BY_ID_WHERE,
            {"post_id": post_id, "me": user_id},
            {"method": "one"},
        )

    def create_post(self, data: Dict[str, Any]) -> dict:
        return self.crud.create("posts", data)

    def update_post(self, post_id: int, changes: Dict[str, Any]) -> dict:
        return self.crud.update("posts", changes, {"id": post_id})

    def delete_post(self, post_id: int) -> None:
        self.crud.delete("posts", {"id": post_id})

    def feed_page(self, user_id: int, cursor: Optional[int], size: int) -> dict:
        return self._page(POST_SELECT + FEED_WHERE, {"me": user_id}, cursor, size)

    def post_likers_page(self, post_id: int, cursor: Optional[int], size: int) -> dict:
        return self._page(
            POST_LIKERS_SELECT, {"post_id": post_id}, cursor, size, id_field="u.id"
        )

    def find_comment(self, comment_id: int) -> Optional[dict]:
        return self.crud.find_first("comments", {"id": comment_id, "is_active": True})

    def create_comment(self, data: Dict[str, Any]) -> dict:
        return self.crud.create("comments", data)

    def update_comment(self, comment_id: int, content: str) -> dict:
        return self.crud.update("comments", {"content": content}, {"id": comment_id})

    def delete_comment(self, comment_id: int) -> None:
        self.crud.delete("comments", {"id": comment_id})

    def comments_page(self, post_id: int, user_id: int, cursor: Optional[int],
                      size: int) -> dict:
        return self._page(
            COMMENT_SELECT + TOP_LEVEL_COMMENTS_WHERE,
            {"post_id": post_id, "me": user_id},
            cursor, size, id_field="c.id",
        )

    def replies_page(self, comment_id: int, user_id: int, cursor: Optional[int],
                     size: int) -> dict:
        return self._page(
            COMMENT_SELECT + REPLIES_WHERE,
            {"parent_id": comment_id, "me": user_id},
            cursor, size, id_field="c.id", descending=False,
        )

    def toggle_reaction(self, table: str, target_col: str, target_id: int,
                        user_id: int) -> bool:
        inserted = self.crud.execute_query(
            REACT_INSERT.format(table=table, target_col=target_col),
            {"target_id": target_id, "user_id": user_id},
            {"method": "one"},
        )
        if inserted:
            self.crud.db.commit()
            return True
        self.crud.delete(
            table, {target_col: target_id, "user_id": user_id}, returning="user_id"
        )
        return False
