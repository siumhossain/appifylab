"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Avatar } from "@/components/feed/avatar";
import { DeleteConfirm } from "@/components/feed/delete-confirm";
import { Spinner } from "@/components/auth/ui";
import { usePaged } from "@/hooks/use-paged";
import { useReaction } from "@/hooks/use-reaction";
import { apiErrorMessage } from "@/lib/api/client";
import { postsApi, type Comment } from "@/lib/api/posts";
import { useAuthStore } from "@/store/auth";
import { cn, timeAgo } from "@/lib/utils";

function useCommentDraft(onSubmit: (content: string) => Promise<void>) {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const content = draft.trim();
    if (!content || busy) return;
    setBusy(true);
    setError(null);
    try {
      await onSubmit(content);
      setDraft("");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return { draft, setDraft, busy, error, submit };
}

function useMyComment() {
  const user = useAuthStore((s) => s.user);
  return useCallback(
    (created: Comment): Comment => ({
      ...created,
      first_name: user?.first_name ?? "",
      last_name: user?.last_name ?? "",
      is_owner: true,
      reacted: false,
    }),
    [user]
  );
}

function CommentForm({
  placeholder,
  onSubmit,
  autoFocus = false,
}: {
  placeholder: string;
  onSubmit: (content: string) => Promise<void>;
  autoFocus?: boolean;
}) {
  const form = useCommentDraft(onSubmit);
  const canSend = !form.busy && form.draft.trim().length > 0;
  return (
    <form onSubmit={form.submit} className="space-y-1">
      <div className="flex items-center gap-2 rounded-full border border-border/60 bg-muted/40 py-1 pr-1 pl-4 transition-colors focus-within:border-ring">
        <input
          value={form.draft}
          onChange={(e) => form.setDraft(e.target.value)}
          placeholder={placeholder}
          maxLength={5000}
          disabled={form.busy}
          autoFocus={autoFocus}
          className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!canSend}
          className={cn(
            "flex h-7 shrink-0 cursor-pointer items-center rounded-full px-3.5 text-xs font-semibold text-white transition-all",
            canSend ? "bg-sky-500 hover:bg-sky-600 active:scale-95" : "pointer-events-none bg-sky-500/40"
          )}
        >
          {form.busy ? <Spinner /> : "Send"}
        </button>
      </div>
      {form.error && <p className="px-2 text-xs text-destructive">{form.error}</p>}
    </form>
  );
}

function EditForm({
  initial,
  onSave,
  onCancel,
}: {
  initial: string;
  onSave: (content: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canSave = !busy && value.trim().length > 0 && value.trim() !== initial;

  async function save() {
    if (!canSave) return;
    setBusy(true);
    setError(null);
    try {
      await onSave(value.trim());
    } catch (err) {
      setError(apiErrorMessage(err));
      setBusy(false);
    }
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 rounded-full border border-border/60 bg-muted/40 py-1 pr-1 pl-4 transition-colors focus-within:border-ring">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") save();
            if (e.key === "Escape") onCancel();
          }}
          maxLength={5000}
          disabled={busy}
          autoFocus
          className="w-full bg-transparent text-sm outline-none disabled:opacity-50"
        />
        <button
          type="button"
          onClick={save}
          disabled={!canSave}
          className={cn(
            "flex h-7 shrink-0 cursor-pointer items-center rounded-full px-3.5 text-xs font-semibold text-white transition-all",
            canSave ? "bg-sky-500 hover:bg-sky-600 active:scale-95" : "pointer-events-none bg-sky-500/40"
          )}
        >
          {busy ? <Spinner /> : "Save"}
        </button>
      </div>
      <div className="flex items-center gap-3 px-2 text-xs text-muted-foreground">
        <button type="button" onClick={onCancel} disabled={busy} className="cursor-pointer font-medium transition-colors hover:text-foreground">
          Cancel
        </button>
        <span className="hidden sm:inline">Enter to save · Esc to cancel</span>
      </div>
      {error && <p className="px-2 text-xs text-destructive">{error}</p>}
    </div>
  );
}

function CommentBody({
  comment,
  onDelete,
  onEdit,
  children,
}: {
  comment: Comment;
  onDelete: () => Promise<void>;
  onEdit: (content: string) => Promise<void>;
  children?: React.ReactNode;
}) {
  const reaction = useReaction(
    { reacted: comment.reacted, count: comment.reaction_count },
    () => postsApi.reactComment(comment.id)
  );
  const [deleting, setDeleting] = useState(false);
  const [editing, setEditing] = useState(false);

  async function remove() {
    if (deleting) return;
    setDeleting(true);
    try {
      await onDelete();
    } catch {
      setDeleting(false);
    }
  }

  return (
    <div className={cn("flex gap-2.5", deleting && "opacity-50")}>
      <Avatar
        firstName={comment.first_name}
        lastName={comment.last_name}
        className="size-7 text-[10px]"
      />
      <div className="min-w-0 flex-1">
        {editing ? (
          <EditForm
            initial={comment.content}
            onCancel={() => setEditing(false)}
            onSave={async (content) => {
              await onEdit(content);
              setEditing(false);
            }}
          />
        ) : (
          <>
            <p className="text-sm leading-snug break-words">
              <span className="font-semibold">
                {comment.first_name} {comment.last_name}
              </span>{" "}
              <span className="whitespace-pre-wrap">{comment.content}</span>
            </p>
            <div className="mt-1 flex items-center gap-3 text-xs font-medium text-muted-foreground">
              <span className="font-normal">{timeAgo(comment.created_at)}</span>
              {reaction.count > 0 && (
                <span className="font-normal">
                  {reaction.count} {reaction.count === 1 ? "like" : "likes"}
                </span>
              )}
              {children}
              {comment.is_owner && (
                <>
                  <button
                    type="button"
                    onClick={() => setEditing(true)}
                    className="cursor-pointer transition-colors hover:text-foreground"
                  >
                    Edit
                  </button>
                  <DeleteConfirm
                    title="Delete this comment?"
                    onConfirm={remove}
                    trigger={
                      <button
                        type="button"
                        disabled={deleting}
                        className="cursor-pointer transition-colors hover:text-destructive"
                      >
                        Delete
                      </button>
                    }
                  />
                </>
              )}
            </div>
          </>
        )}
      </div>
      <button
        type="button"
        aria-label={reaction.reacted ? "Unlike" : "Like"}
        onClick={reaction.toggle}
        className={cn(
          "mt-1 shrink-0 cursor-pointer self-start transition-all active:scale-75",
          reaction.reacted ? "text-rose-500" : "text-muted-foreground hover:text-foreground"
        )}
      >
        <svg viewBox="0 0 24 24" fill={reaction.reacted ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-3.5">
          <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
        </svg>
      </button>
    </div>
  );
}

function Replies({
  parent,
  onReplyCountDelta,
}: {
  parent: Comment;
  onReplyCountDelta: (delta: number) => void;
}) {
  const asMine = useMyComment();
  const fetcher = useCallback(
    (cursor: number | null) => postsApi.replies(parent.id, cursor),
    [parent.id]
  );
  const page = usePaged<Comment>(fetcher);
  const { reset } = page;

  useEffect(() => {
    void reset();
  }, [reset]);

  async function addReply(content: string) {
    const created = await postsApi.addComment(parent.post_id, content, parent.id);
    page.setItems((prev) => [...prev, asMine(created)]);
    onReplyCountDelta(1);
  }

  async function deleteReply(reply: Comment) {
    await postsApi.removeComment(reply.id);
    page.setItems((prev) => prev.filter((r) => r.id !== reply.id));
    onReplyCountDelta(-1);
  }

  async function editReply(reply: Comment, content: string) {
    await postsApi.updateComment(reply.id, content);
    page.setItems((prev) => prev.map((r) => (r.id === reply.id ? { ...r, content } : r)));
  }

  return (
    <div className="mt-2 ml-9 space-y-3">
      {page.items.map((reply) => (
        <CommentBody
          key={reply.id}
          comment={reply}
          onDelete={() => deleteReply(reply)}
          onEdit={(content) => editReply(reply, content)}
        />
      ))}
      {page.loading && (
        <div className="flex justify-center py-1 text-muted-foreground">
          <Spinner />
        </div>
      )}
      {page.error && <p className="text-xs text-destructive">{page.error}</p>}
      {page.hasMore && !page.loading && (
        <button
          type="button"
          onClick={page.loadMore}
          className="flex cursor-pointer items-center gap-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <span className="h-px w-6 bg-border" />
          View more replies
        </button>
      )}
      <CommentForm placeholder="Write a reply..." onSubmit={addReply} autoFocus />
    </div>
  );
}

function CommentItem({
  comment,
  onDeleted,
  onEdited,
}: {
  comment: Comment;
  onDeleted: (comment: Comment) => Promise<void>;
  onEdited: (comment: Comment, content: string) => Promise<void>;
}) {
  const [repliesOpen, setRepliesOpen] = useState(false);
  const [replyCount, setReplyCount] = useState(comment.reply_count);

  return (
    <div>
      <CommentBody
        comment={comment}
        onDelete={() => onDeleted(comment)}
        onEdit={(content) => onEdited(comment, content)}
      >
        <button
          type="button"
          onClick={() => setRepliesOpen((v) => !v)}
          className="cursor-pointer transition-colors hover:text-foreground"
        >
          Reply{replyCount > 0 && ` (${replyCount})`}
        </button>
      </CommentBody>
      {repliesOpen && (
        <Replies parent={comment} onReplyCountDelta={(d) => setReplyCount((c) => c + d)} />
      )}
    </div>
  );
}

export function Comments({
  postId,
  onCountDelta,
}: {
  postId: number;
  onCountDelta: (delta: number) => void;
}) {
  const asMine = useMyComment();
  const fetcher = useCallback(
    (cursor: number | null) => postsApi.comments(postId, cursor),
    [postId]
  );
  const page = usePaged<Comment>(fetcher);
  const { reset } = page;

  useEffect(() => {
    void reset();
  }, [reset]);

  async function addComment(content: string) {
    const created = await postsApi.addComment(postId, content);
    page.setItems((prev) => [asMine(created), ...prev]);
    onCountDelta(1);
  }

  async function deleteComment(comment: Comment) {
    await postsApi.removeComment(comment.id);
    page.setItems((prev) => prev.filter((c) => c.id !== comment.id));
    onCountDelta(-1);
  }

  async function editComment(comment: Comment, content: string) {
    await postsApi.updateComment(comment.id, content);
    page.setItems((prev) => prev.map((c) => (c.id === comment.id ? { ...c, content } : c)));
  }

  return (
    <div className="space-y-4 border-t border-border/60 pt-3">
      <CommentForm placeholder="Add a comment..." onSubmit={addComment} />
      {page.items.map((comment) => (
        <CommentItem
          key={comment.id}
          comment={comment}
          onDeleted={deleteComment}
          onEdited={editComment}
        />
      ))}
      {page.loading && (
        <div className="flex justify-center py-1 text-muted-foreground">
          <Spinner />
        </div>
      )}
      {page.error && <p className="text-xs text-destructive">{page.error}</p>}
      {page.hasMore && !page.loading && (
        <button
          type="button"
          onClick={page.loadMore}
          className="flex cursor-pointer items-center gap-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <span className="h-px w-6 bg-border" />
          View more comments
        </button>
      )}
    </div>
  );
}
