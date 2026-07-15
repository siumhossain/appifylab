type Envelope<T> = { results: T; message: string; pagination?: Pagination };

export type Pagination = { has_more: boolean; next_cursor: number | null; size: number };
export type Page<T> = { items: T[]; pagination: Pagination };

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

export function apiErrorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
}

async function request<T>(path: string, init?: RequestInit): Promise<Envelope<T>> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
      credentials: "same-origin",
    });
  } catch {
    throw new ApiError("Network error. Check your connection and try again.", 0);
  }

  const body = (await res.json().catch(() => null)) as Envelope<T> | null;
  if (!res.ok) {
    throw new ApiError(body?.message || "Something went wrong. Please try again.", res.status);
  }
  if (!body) {
    throw new ApiError("Unexpected server response.", res.status);
  }
  return body;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  return (await request<T>(path, init)).results;
}

export async function apiPage<T>(path: string, init?: RequestInit): Promise<Page<T>> {
  const body = await request<T[]>(path, init);
  return {
    items: body.results ?? [],
    pagination: body.pagination ?? { has_more: false, next_cursor: null, size: 0 },
  };
}
