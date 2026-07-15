"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/feed/avatar";
import { Composer } from "@/components/feed/composer";
import { PostCard } from "@/components/feed/post-card";
import { Spinner } from "@/components/auth/ui";
import { usePaged } from "@/hooks/use-paged";
import { postsApi, type Post } from "@/lib/api/posts";
import { useAuthStore } from "@/store/auth";

function PostSkeleton() {
  return (
    <div className="animate-pulse space-y-3 rounded-2xl border border-border/60 bg-card p-4">
      <div className="flex items-center gap-3">
        <div className="size-9 rounded-full bg-muted" />
        <div className="space-y-1.5">
          <div className="h-3 w-32 rounded-full bg-muted" />
          <div className="h-2.5 w-16 rounded-full bg-muted" />
        </div>
      </div>
      <div className="h-3 w-3/4 rounded-full bg-muted" />
      <div className="aspect-[4/3] rounded-xl bg-muted" />
    </div>
  );
}

export default function HomePage() {
  const router = useRouter();
  const { user, loadMe, logout } = useAuthStore();
  const [checking, setChecking] = useState(true);
  const feed = usePaged<Post>(postsApi.feed);
  const { reset, loadMore, hasMore, loading } = feed;
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadMe().then((ok) => {
      if (!ok) router.replace("/login");
      else setChecking(false);
    });
  }, [loadMe, router]);

  useEffect(() => {
    if (!checking) void reset();
  }, [checking, reset]);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el || checking || !hasMore || loading || feed.error) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) void loadMore();
      },
      { rootMargin: "400px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [checking, hasMore, loading, feed.error, loadMore]);

  if (checking || !user) {
    return (
      <main className="flex min-h-svh items-center justify-center text-muted-foreground">
        <Spinner />
      </main>
    );
  }

  const initialLoading = loading && feed.items.length === 0;

  return (
    <div className="min-h-svh bg-neutral-50 dark:bg-background">
      <header className="sticky top-0 z-10 border-b border-border/60 bg-background/70 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-xl items-center justify-between px-4">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-xl bg-gradient-to-tr from-amber-400 via-rose-500 to-purple-600 text-white shadow-sm">
              <svg viewBox="0 0 24 24" fill="currentColor" className="size-3.5">
                <polygon points="6 3 20 12 6 21 6 3" />
              </svg>
            </div>
            <span className="text-lg font-bold tracking-tight">Feed</span>
          </div>
          <div className="flex items-center gap-2.5">
            <Avatar
              firstName={user.first_name}
              lastName={user.last_name}
              className="size-8 text-[11px]"
            />
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground"
              onClick={async () => {
                await logout();
                router.replace("/login");
              }}
            >
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-xl space-y-4 px-4 py-5">
        <Composer onCreated={() => void reset()} />

        {feed.items.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            onDeleted={(id) => feed.setItems((prev) => prev.filter((p) => p.id !== id))}
          />
        ))}

        {initialLoading && (
          <>
            <PostSkeleton />
            <PostSkeleton />
          </>
        )}

        {feed.error && (
          <div className="space-y-2 rounded-2xl border border-border/60 bg-card py-6 text-center text-sm text-destructive">
            <p>{feed.error}</p>
            <Button variant="outline" size="sm" onClick={() => void loadMore()}>
              Retry
            </Button>
          </div>
        )}

        <div ref={sentinelRef} />

        {loading && !initialLoading && (
          <div className="flex justify-center py-4 text-muted-foreground">
            <Spinner />
          </div>
        )}

        {!hasMore && !loading && feed.items.length > 0 && (
          <div className="flex items-center gap-3 py-6 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            <span className="h-px flex-1 bg-border" />
            You&apos;re all caught up
            <span className="h-px flex-1 bg-border" />
          </div>
        )}

        {!hasMore && !loading && feed.items.length === 0 && !feed.error && (
          <div className="rounded-2xl border border-border/60 bg-card py-14 text-center">
            <div className="mx-auto mb-3 flex size-12 items-center justify-center rounded-full bg-gradient-to-tr from-amber-400 via-rose-500 to-purple-600 text-white">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-5">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="9" cy="9" r="2" />
                <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
              </svg>
            </div>
            <p className="text-sm font-semibold">No posts yet</p>
            <p className="mt-1 text-sm text-muted-foreground">Be the first to share something.</p>
          </div>
        )}
      </main>
    </div>
  );
}
