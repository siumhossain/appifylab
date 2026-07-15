import { api } from "@/lib/api/client";

export type User = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  created_at: string;
};

export type LoginPayload = { email: string; password: string };

export type SignupPayload = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
};

export const authApi = {
  login: (payload: LoginPayload) =>
    api<{ user: User }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  register: (payload: SignupPayload) =>
    api<{ user: User }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  logout: () => api<null>("/api/auth/logout", { method: "POST" }),
  me: () => api<User>("/api/backend/users/me"),
};
