"use client";

import { useRef, useState } from "react";

export function useReaction(
  initial: { reacted: boolean; count: number },
  call: () => Promise<{ reacted: boolean }>
) {
  const [state, setState] = useState(initial);
  const busyRef = useRef(false);

  async function toggle() {
    if (busyRef.current) return;
    busyRef.current = true;
    const prev = state;
    const next = { reacted: !prev.reacted, count: prev.count + (prev.reacted ? -1 : 1) };
    setState(next);
    try {
      const { reacted } = await call();
      if (reacted !== next.reacted) {
        setState({ reacted, count: prev.count + (reacted ? 1 : -1) });
      }
    } catch {
      setState(prev);
    } finally {
      busyRef.current = false;
    }
  }

  return { ...state, toggle };
}
