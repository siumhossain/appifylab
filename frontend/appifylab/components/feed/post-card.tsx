"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Avatar } from "@/components/feed/avatar";
import { Comments } from "@/components/feed/comments";
import { DeleteConfirm } from "@/components/feed/delete-confirm";
import { Spinner } from "@/components/auth/ui";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { usePaged } from "@/hooks/use-paged";
import { useReaction } from "@/hooks/use-reaction";
import { apiErrorMessage } from "@/lib/api/client";
import { postsApi, type Liker, type Post } from "@/lib/api/posts";
import { cn, timeAgo } from "@/lib/utils";

function FeedImage({ src, className }: { src: string; className?: string }) {
  const [loaded, setLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (imgRef.current?.complete) setLoaded(true);
  }, []);

  return (
    <div className={cn("relative overflow-hidden bg-muted", className)}>
      <div
        aria-hidden
        className={cn(
          "absolute inset-0 -translate-x-full animate-[shimmer_1.4s_infinite] bg-gradient-to-r from-transparent via-foreground/6 to-transparent transition-opacity",
          loaded && "opacity-0"
        )}
      />
      <img
        ref={imgRef}
        src={src}
        alt=""
        loading="lazy"
        decoding="async"
        onLoad={() => setLoaded(true)}
        className={cn(
          "size-full object-cover transition-[opacity,transform] duration-700 ease-out",
          loaded ? "scale-100 opacity-100" : "scale-[1.03] opacity-0"
        )}
      />
    </div>
  );
}

function PostImages({ urls }: { urls: string[] }) {
  if (urls.length === 0) return null;
  if (urls.length === 1) {
    return <FeedImage src={urls[0]} className="aspect-[4/3] w-full" />;
  }
  return (
    <div className="relative">
      <div className="flex snap-x snap-mandatory overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {urls.map((url) => (
          <FeedImage key={url} src={url} className="aspect-square w-full shrink-0 snap-center" />
        ))}
      </div>
      <span className="pointer-events-none absolute top-3 right-3 rounded-full bg-black/60 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-sm">
        {urls.length} photos
      </span>
    </div>
  );
}

function Likers({ postId }: { postId: number }) {
  const fetcher = useCallback(
    (cursor: number | null) => postsApi.likers(postId, cursor),
    [postId]
  );
  const page = usePaged<Liker>(fetcher);
  const { reset } = page;

  useEffect(() => {
    void reset();
  }, [reset]);

  return (
    <div className="max-h-80 space-y-3 overflow-y-auto px-4 pt-3 pb-4">
      {page.items.map((liker) => (
        <div key={liker.id} className="flex items-center gap-3">
          <Avatar firstName={liker.first_name} lastName={liker.last_name} className="size-9 text-xs" />
          <span className="text-sm font-medium">
            {liker.first_name} {liker.last_name}
          </span>
        </div>
      ))}
      {page.loading && (
        <div className="flex justify-center py-2 text-muted-foreground">
          <Spinner />
        </div>
      )}
      {page.error && <p className="text-xs text-destructive">{page.error}</p>}
      {page.hasMore && !page.loading && (
        <button
          type="button"
          onClick={page.loadMore}
          className="cursor-pointer text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          Show more
        </button>
      )}
    </div>
  );
}

export function PostCard({ post, onDeleted }: { post: Post; onDeleted: (id: number) => void }) {
  const reaction = useReaction(
    { reacted: post.reacted, count: post.reaction_count },
    () => postsApi.react(post.id)
  );
  const [commentsOpen, setCommentsOpen] = useState(false);
  const [commentCount, setCommentCount] = useState(post.comment_count);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function remove() {
    if (deleting) return;
    setDeleting(true);
    setError(null);
    try {
      await postsApi.remove(post.id);
      onDeleted(post.id);
    } catch (err) {
      setError(apiErrorMessage(err));
      setDeleting(false);
    }
  }

  return (
    <article
      className={cn(
        "overflow-hidden rounded-2xl border border-border/60 bg-card shadow-[0_1px_3px_rgb(0_0_0/0.04),0_8px_24px_-12px_rgb(0_0_0/0.08)] transition-opacity",
        deleting && "opacity-50"
      )}
    >
      <div className="flex items-center gap-3 px-4 py-3">
        <Avatar firstName={post.first_name} lastName={post.last_name} ring className="size-8 text-[11px]" />
        <div className="min-w-0">
          <p className="truncate text-sm leading-tight font-semibold">
            {post.first_name} {post.last_name}
            <span className="font-normal text-muted-foreground"> · {timeAgo(post.created_at)}</span>
          </p>
          {post.privacy === "private" && (
            <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-3">
                <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              Only you
            </p>
          )}
        </div>
        {post.is_owner && (
          <DeleteConfirm
            title="Delete this post?"
            onConfirm={remove}
            trigger={
              <button
                type="button"
                aria-label="Delete post"
                disabled={deleting}
                className="ml-auto cursor-pointer rounded-full p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-destructive"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-4">
                  <path d="M3 6h18" />
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                </svg>
              </button>
            }
          />
        )}
      </div>

      {post.content && (
        <p className="px-4 pb-3 text-[15px] leading-relaxed break-words whitespace-pre-wrap">
          {post.content}
        </p>
      )}

      <PostImages urls={post.image_urls} />

      {error && <p className="px-4 pt-2 text-xs text-destructive">{error}</p>}

      <div className="flex items-center gap-3 px-4 pt-3">
        <button
          type="button"
          aria-label={reaction.reacted ? "Unlike" : "Like"}
          onClick={reaction.toggle}
          className={cn(
            "cursor-pointer transition-all duration-150 active:scale-75",
            reaction.reacted ? "text-rose-500" : "text-foreground hover:text-muted-foreground"
          )}
        >
          <svg viewBox="0 0 24 24" fill={reaction.reacted ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="size-6.5">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
          </svg>
        </button>
        <button
          type="button"
          aria-label="Comments"
          onClick={() => setCommentsOpen((v) => !v)}
          className="cursor-pointer text-foreground transition-all duration-150 hover:text-muted-foreground active:scale-75"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="size-6.5">
            <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
          </svg>
        </button>
      </div>

      {reaction.count > 0 && (
        <div className="px-4 pt-2">
          <Dialog>
            <DialogTrigger className="cursor-pointer text-sm font-semibold transition-colors hover:underline">
              {reaction.count} {reaction.count === 1 ? "like" : "likes"}
            </DialogTrigger>
            <DialogContent>
              <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
                <DialogTitle>Likes</DialogTitle>
                <DialogClose
                  aria-label="Close"
                  className="cursor-pointer rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-4">
                    <path d="M18 6 6 18" />
                    <path d="m6 6 12 12" />
                  </svg>
                </DialogClose>
              </div>
              <Likers postId={post.id} />
            </DialogContent>
          </Dialog>
        </div>
      )}

      {!commentsOpen && commentCount > 0 && (
        <button
          type="button"
          onClick={() => setCommentsOpen(true)}
          className="cursor-pointer px-4 pt-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          View all {commentCount} {commentCount === 1 ? "comment" : "comments"}
        </button>
      )}

      <div className={cn("px-4", commentsOpen ? "pt-3 pb-4" : "pb-4")}>
        {commentsOpen && (
          <Comments postId={post.id} onCountDelta={(d) => setCommentCount((c) => c + d)} />
        )}
      </div>
    </article>
  );
}
