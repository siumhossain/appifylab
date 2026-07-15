import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import { authApi, type LoginPayload, type SignupPayload, type User } from "@/lib/api/auth";

type AuthState = {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<boolean>;
  register: (payload: SignupPayload) => Promise<boolean>;
  loadMe: () => Promise<boolean>;
  logout: () => Promise<void>;
  clearError: () => void;
};

function toMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
}

export const useAuthStore = create<AuthState>((set) => {
  const authenticate = async (request: () => Promise<{ user: User }>) => {
    set({ loading: true, error: null });
    try {
      const { user } = await request();
      set({ user, loading: false });
      return true;
    } catch (err) {
      set({ loading: false, error: toMessage(err) });
      return false;
    }
  };

  return {
    user: null,
    loading: false,
    error: null,

    login: (payload) =>
      authenticate(() =>
        authApi.login({ email: payload.email.trim().toLowerCase(), password: payload.password })
      ),

    register: (payload) =>
      authenticate(() =>
        authApi.register({
          first_name: payload.first_name.trim(),
          last_name: payload.last_name.trim(),
          email: payload.email.trim().toLowerCase(),
          password: payload.password,
        })
      ),

    loadMe: async () => {
      try {
        const user = await authApi.me();
        set({ user });
        return true;
      } catch {
        set({ user: null });
        return false;
      }
    },

    logout: async () => {
      try {
        await authApi.logout();
      } finally {
        set({ user: null, error: null });
      }
    },

    clearError: () => set({ error: null }),
  };
});
