"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Avatar } from "@/components/feed/avatar";
import { ErrorBanner, Spinner } from "@/components/auth/ui";
import { apiErrorMessage } from "@/lib/api/client";
import {
  MAX_IMAGES_PER_POST,
  MAX_IMAGE_SIZE,
  postsApi,
  uploadImages,
  type Privacy,
} from "@/lib/api/posts";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

export function Composer({ onCreated }: { onCreated: () => void }) {
  const user = useAuthStore((s) => s.user);
  const [content, setContent] = useState("");
  const [privacy, setPrivacy] = useState<Privacy>("public");
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(() => () => previews.forEach((url) => URL.revokeObjectURL(url)), [previews]);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const picked = Array.from(list).filter((f) => f.type.startsWith("image/"));
    const oversize = picked.find((f) => f.size > MAX_IMAGE_SIZE);
    if (oversize) {
      setError(`${oversize.name} is over 10 MB.`);
      return;
    }
    setError(null);
    setFiles((prev) => [...prev, ...picked].slice(0, MAX_IMAGES_PER_POST));
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const image_urls = files.length ? await uploadImages(files) : [];
      await postsApi.create({ content: content.trim(), image_urls, privacy });
      setContent("");
      setFiles([]);
      setPrivacy("public");
      onCreated();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const canPost = !busy && (content.trim().length > 0 || files.length > 0);

  return (
    <section className="rounded-2xl border border-border/60 bg-card shadow-[0_1px_3px_rgb(0_0_0/0.04),0_8px_24px_-12px_rgb(0_0_0/0.08)]">
      <div className="flex gap-3 px-4 pt-4">
        <Avatar
          firstName={user?.first_name ?? ""}
          lastName={user?.last_name ?? ""}
          className="size-9 text-xs"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={`What's on your mind, ${user?.first_name ?? "there"}?`}
          rows={2}
          maxLength={10000}
          disabled={busy}
          className="min-h-14 w-full resize-none bg-transparent pt-1.5 text-[15px] outline-none placeholder:text-muted-foreground disabled:opacity-50"
        />
      </div>

      {previews.length > 0 && (
        <div className="flex flex-wrap gap-2 px-4 pt-3">
          {previews.map((url, i) => (
            <div key={url} className="relative">
              <img src={url} alt="" className="size-20 rounded-xl object-cover" />
              <button
                type="button"
                aria-label="Remove image"
                disabled={busy}
                onClick={() => setFiles((prev) => prev.filter((_, j) => j !== i))}
                className="absolute -top-1.5 -right-1.5 flex size-5 cursor-pointer items-center justify-center rounded-full bg-foreground text-xs text-background shadow-md transition-transform hover:scale-110"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="px-4 pt-3">
          <ErrorBanner message={error} />
        </div>
      )}

      <div className="mt-3 flex items-center gap-2 border-t border-border/60 px-3 py-2.5">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          multiple
          hidden
          onChange={(e) => {
            addFiles(e.target.files);
            e.target.value = "";
          }}
        />
        <button
          type="button"
          disabled={busy || files.length >= MAX_IMAGES_PER_POST}
          onClick={() => fileInputRef.current?.click()}
          className="flex cursor-pointer items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-4.5 text-emerald-500">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="9" cy="9" r="2" />
            <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
          </svg>
          Photos
        </button>

        <select
          value={privacy}
          onChange={(e) => setPrivacy(e.target.value as Privacy)}
          disabled={busy}
          aria-label="Post privacy"
          className="h-8 cursor-pointer rounded-full bg-muted px-3 text-xs font-medium outline-none transition-colors hover:bg-muted/70 focus-visible:ring-2 focus-visible:ring-ring/50 disabled:opacity-50"
        >
          <option value="public">🌐 Public</option>
          <option value="private">🔒 Private</option>
        </select>

        <button
          type="button"
          disabled={!canPost}
          onClick={submit}
          className={cn(
            "ml-auto flex h-8 cursor-pointer items-center gap-1.5 rounded-full bg-sky-500 px-5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-sky-600 active:scale-95",
            !canPost && "pointer-events-none opacity-40"
          )}
        >
          {busy && <Spinner />}
          Post
        </button>
      </div>
    </section>
  );
}
