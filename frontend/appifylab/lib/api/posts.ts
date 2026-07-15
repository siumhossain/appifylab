import { ApiError, api, apiPage, type Page } from "@/lib/api/client";

export type Privacy = "public" | "private";

export type Post = {
  id: number;
  user_id: number;
  content: string;
  image_urls: string[];
  privacy: Privacy;
  reaction_count: number;
  comment_count: number;
  created_at: string;
  first_name: string;
  last_name: string;
  is_owner: boolean;
  reacted: boolean;
};

export type Comment = {
  id: number;
  post_id: number;
  user_id: number;
  parent_comment_id: number | null;
  content: string;
  reaction_count: number;
  reply_count: number;
  created_at: string;
  first_name: string;
  last_name: string;
  is_owner: boolean;
  reacted: boolean;
};

export type Liker = {
  id: number;
  first_name: string;
  last_name: string;
};

export type PostCreatePayload = {
  content: string;
  image_urls: string[];
  privacy: Privacy;
};

const BASE = "/api/backend";

const withCursor = (path: string, cursor: number | null) =>
  `${BASE}${path}${cursor ? `?cursor=${cursor}` : ""}`;

export const postsApi = {
  feed: (cursor: number | null): Promise<Page<Post>> =>
    apiPage<Post>(withCursor("/posts", cursor)),

  create: (payload: PostCreatePayload) =>
    api<Post>(`${BASE}/posts`, { method: "POST", body: JSON.stringify(payload) }),

  remove: (postId: number) =>
    api<{ deleted: boolean }>(`${BASE}/posts/${postId}`, { method: "DELETE" }),

  react: (postId: number) =>
    api<{ reacted: boolean }>(`${BASE}/posts/${postId}/react`, { method: "POST" }),

  likers: (postId: number, cursor: number | null): Promise<Page<Liker>> =>
    apiPage<Liker>(withCursor(`/posts/${postId}/likes`, cursor)),

  comments: (postId: number, cursor: number | null): Promise<Page<Comment>> =>
    apiPage<Comment>(withCursor(`/posts/${postId}/comments`, cursor)),

  replies: (commentId: number, cursor: number | null): Promise<Page<Comment>> =>
    apiPage<Comment>(withCursor(`/comments/${commentId}/replies`, cursor)),

  addComment: (postId: number, content: string, parentCommentId?: number) =>
    api<Comment>(`${BASE}/posts/${postId}/comments`, {
      method: "POST",
      body: JSON.stringify({ content, parent_comment_id: parentCommentId ?? null }),
    }),

  updateComment: (commentId: number, content: string) =>
    api<Comment>(`${BASE}/comments/${commentId}`, {
      method: "PATCH",
      body: JSON.stringify({ content }),
    }),

  removeComment: (commentId: number) =>
    api<{ deleted: boolean }>(`${BASE}/comments/${commentId}`, { method: "DELETE" }),

  reactComment: (commentId: number) =>
    api<{ reacted: boolean }>(`${BASE}/comments/${commentId}/react`, { method: "POST" }),
};

type PresignedUpload = {
  upload_url: string;
  key: string;
  public_url: string;
  expires_in: number;
};

export const MAX_IMAGE_SIZE = 10 * 1024 * 1024;
export const MAX_IMAGES_PER_POST = 10;

export function uploadImages(files: File[]): Promise<string[]> {
  return Promise.all(
    files.map(async (file) => {
      const { upload_url, public_url } = await api<PresignedUpload>(
        `${BASE}/upload/image/presigned-url`,
        {
          method: "POST",
          body: JSON.stringify({ content_type: file.type, size: file.size }),
        }
      );
      const res = await fetch(upload_url, {
        method: "PUT",
        headers: { "Content-Type": file.type },
        body: file,
      });
      if (!res.ok) throw new ApiError(`Failed to upload ${file.name}.`, res.status);
      return public_url;
    })
  );
}
