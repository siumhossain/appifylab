"use client";

import { useCallback, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { apiErrorMessage, type Page } from "@/lib/api/client";

export type Paged<T> = {
  items: T[];
  setItems: Dispatch<SetStateAction<T[]>>;
  hasMore: boolean;
  loading: boolean;
  error: string | null;
  loadMore: () => Promise<void>;
  reset: () => Promise<void>;
};

export function usePaged<T extends { id: number }>(
  fetcher: (cursor: number | null) => Promise<Page<T>>
): Paged<T> {
  const [items, setItems] = useState<T[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cursorRef = useRef<number | null>(null);
  const busyRef = useRef(false);

  const load = useCallback(
    async (reset: boolean) => {
      if (busyRef.current) return;
      busyRef.current = true;
      setLoading(true);
      setError(null);
      try {
        const page = await fetcher(reset ? null : cursorRef.current);
        cursorRef.current = page.pagination.next_cursor;
        setHasMore(page.pagination.has_more);
        setItems((prev) => (reset ? page.items : [...prev, ...page.items]));
      } catch (err) {
        setError(apiErrorMessage(err));
      } finally {
        busyRef.current = false;
        setLoading(false);
      }
    },
    [fetcher]
  );

  const loadMore = useCallback(() => load(false), [load]);
  const reset = useCallback(() => load(true), [load]);

  return { items, setItems, hasMore, loading, error, loadMore, reset };
}
