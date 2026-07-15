import uuid

from fastapi.testclient import TestClient

import main

suffix = uuid.uuid4().hex[:8]


def register(client, name):
    r = client.post("/users/register", json={
        "first_name": name, "last_name": "Test",
        "email": f"{name}_{suffix}@example.com", "password": "password123",
    })
    assert r.status_code == 201, r.text
    d = r.json()["results"]
    return {"Authorization": f"Bearer {d['access_token']}"}, d["user"]["id"]


with TestClient(main.app) as c:
    alice, alice_id = register(c, "alice")
    bob, bob_id = register(c, "bob")

    r = c.post("/posts", json={"content": "", "image_urls": []}, headers=alice)
    assert r.status_code == 422, "empty post must be rejected"

    r = c.post("/posts", json={"content": "hi", "image_urls": ["https://evil.com/x.png"]}, headers=alice)
    assert r.status_code == 422, "foreign image_url must be rejected"

    r = c.post("/posts", json={"content": "public post"}, headers=alice)
    assert r.status_code == 201, r.text
    pub = r.json()["results"]["id"]

    r = c.post("/posts", json={"content": "secret", "privacy": "private"}, headers=alice)
    priv = r.json()["results"]["id"]

    assert c.get(f"/posts/{priv}", headers=bob).status_code == 404, "private post leaked"
    assert c.get(f"/posts/{priv}", headers=alice).status_code == 200
    assert c.get(f"/posts/{pub}").status_code == 401, "unauthenticated access allowed"

    feed_ids = [p["id"] for p in c.get("/posts", headers=bob).json()["results"]]
    assert pub in feed_ids and priv not in feed_ids, "feed privacy broken"

    assert c.patch(f"/posts/{pub}", json={"content": "hacked"}, headers=bob).status_code == 403
    assert c.patch(f"/posts/{pub}", json={"privacy": "private"}, headers=alice).status_code == 200
    c.patch(f"/posts/{pub}", json={"privacy": "public"}, headers=alice)

    r = c.post(f"/posts/{pub}/comments", json={"content": "nice"}, headers=bob)
    assert r.status_code == 201, r.text
    comment = r.json()["results"]["id"]

    r = c.post(f"/posts/{pub}/comments", json={"content": "thx", "parent_comment_id": comment}, headers=alice)
    assert r.status_code == 201
    reply = r.json()["results"]["id"]

    r = c.post(f"/posts/{pub}/comments", json={"content": "deep", "parent_comment_id": reply}, headers=bob)
    assert r.status_code == 422, "nested reply depth not enforced"

    assert c.post(f"/posts/{priv}/comments", json={"content": "x"}, headers=bob).status_code == 404

    post = c.get(f"/posts/{pub}", headers=alice).json()["results"]
    assert post["comment_count"] == 1, "comment_count must count top-level comments only"

    comments = c.get(f"/posts/{pub}/comments", headers=bob).json()["results"]
    top = next(x for x in comments if x["id"] == comment)
    assert top["reply_count"] == 1
    assert top["is_owner"] is True and top["reacted"] is False
    replies = c.get(f"/comments/{comment}/replies", headers=bob).json()["results"]
    assert [x["id"] for x in replies] == [reply]
    assert replies[0]["is_owner"] is False, "reply ownership flag broken"

    assert c.post(f"/posts/{pub}/react", headers=bob).json()["results"]["reacted"] is True
    post = c.get(f"/posts/{pub}", headers=bob).json()["results"]
    assert post["reaction_count"] == 1 and post["reacted"] is True and post["is_owner"] is False
    assert c.get(f"/posts/{pub}", headers=alice).json()["results"]["is_owner"] is True

    r = c.get(f"/posts/{pub}/likes", headers=alice)
    assert r.status_code == 200, r.text
    body = r.json()
    assert [x["id"] for x in body["results"]] == [bob_id], "likers list broken"
    assert body["pagination"]["has_more"] is False
    assert c.get(f"/posts/{pub}/likes").status_code == 401, "likes must require auth"
    assert c.get(f"/posts/{priv}/likes", headers=bob).status_code == 404, "private post likes leaked"
    assert c.get(f"/posts/{pub}/likes?size=0", headers=alice).status_code == 422
    assert c.post(f"/posts/{pub}/react", headers=bob).json()["results"]["reacted"] is False
    post = c.get(f"/posts/{pub}", headers=bob).json()["results"]
    assert post["reaction_count"] == 0 and post["reacted"] is False

    assert c.post(f"/comments/{comment}/react", headers=alice).json()["results"]["reacted"] is True
    top = next(x for x in c.get(f"/posts/{pub}/comments", headers=alice).json()["results"] if x["id"] == comment)
    assert top["reacted"] is True and top["is_owner"] is False

    assert c.patch(f"/comments/{comment}", json={"content": "edit"}, headers=alice).status_code == 403
    assert c.delete(f"/comments/{reply}", headers=bob).status_code == 403
    assert c.delete(f"/comments/{comment}", headers=alice).status_code == 200, "post owner should delete comments"

    assert c.get(f"/posts/{pub}", headers=alice).json()["results"]["comment_count"] == 0

    r = c.post("/users/register", json={
        "first_name": "carol", "last_name": "Test",
        "email": f"carol_{suffix}@example.com", "password": "password123",
    })
    d = r.json()["results"]
    carol = {"Authorization": f"Bearer {d['access_token']}"}
    carol_id, carol_refresh = d["user"]["id"], d["refresh_token"]

    carol_post = c.post("/posts", json={"content": "carol post"}, headers=carol).json()["results"]["id"]
    carol_comment = c.post(f"/posts/{pub}/comments", json={"content": "carol here"}, headers=carol).json()["results"]["id"]

    from sqlalchemy import text
    from common.database import engine
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET is_active = FALSE WHERE id = :id"), {"id": carol_id})

    assert c.post("/users/refresh", json={"refresh_token": carol_refresh}).status_code == 401, \
        "inactive user refreshed token"
    assert c.post("/users/login", json={
        "email": f"carol_{suffix}@example.com", "password": "password123",
    }).status_code == 401, "inactive user logged in"
    assert c.get("/users/me", headers=carol).status_code == 404

    assert carol_post not in [p["id"] for p in c.get("/posts", headers=alice).json()["results"]], \
        "inactive user's post in feed"
    assert c.get(f"/posts/{carol_post}", headers=alice).status_code == 404
    assert carol_comment not in [x["id"] for x in c.get(f"/posts/{pub}/comments", headers=alice).json()["results"]], \
        "inactive user's comment visible"

    with engine.begin() as conn:
        conn.execute(text("UPDATE posts SET is_active = FALSE WHERE id = :id"), {"id": pub})
    assert c.get(f"/posts/{pub}", headers=alice).status_code == 404, "inactive post visible"
    with engine.begin() as conn:
        conn.execute(text("UPDATE posts SET is_active = TRUE WHERE id = :id"), {"id": pub})

    assert c.delete(f"/posts/{pub}", headers=bob).status_code == 403
    assert c.delete(f"/posts/{pub}", headers=alice).status_code == 200
    assert c.get(f"/posts/{pub}", headers=alice).status_code == 404

    r = c.post("/upload/image/presigned-url", json={"content_type": "image/png", "size": 1024})
    assert r.status_code == 401, "upload must require auth"
    r = c.post("/upload/image/presigned-url", json={"content_type": "image/png", "size": 1024}, headers=alice)
    assert r.status_code == 200 and "upload_url" in r.json()["results"], r.text
    r = c.post("/upload/image/presigned-url", json={"content_type": "image/png", "size": 99 * 1024 * 1024}, headers=alice)
    assert r.status_code == 422, "oversize image accepted"
    r = c.post("/upload/video/presigned-url", json={"content_type": "application/pdf", "size": 1}, headers=alice)
    assert r.status_code == 422, "bad content_type accepted"

    c.delete(f"/posts/{priv}", headers=alice)

print("ALL CHECKS PASSED")
