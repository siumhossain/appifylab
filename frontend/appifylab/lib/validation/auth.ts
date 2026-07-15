import type { LoginPayload, SignupPayload } from "@/lib/api/auth";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export type FieldErrors<T> = Partial<Record<keyof T, string>>;
export type LoginErrors = FieldErrors<LoginPayload>;

export type SignupValues = SignupPayload & { confirm_password: string };
export type SignupErrors = FieldErrors<SignupValues>;

function emailError(email: string): string | undefined {
  if (!email) return "Email is required";
  if (email.length > 254) return "Email is too long";
  if (!EMAIL_RE.test(email)) return "Enter a valid email address";
}

function passwordError(password: string): string | undefined {
  if (!password) return "Password is required";
  if (password.length < 8) return "Password must be at least 8 characters";
  if (password.length > 128) return "Password must be at most 128 characters";
}

function nameError(value: string, label: string): string | undefined {
  if (!value.trim()) return `${label} is required`;
  if (value.trim().length > 100) return `${label} must be at most 100 characters`;
}

export function validateLogin(values: LoginPayload): LoginErrors {
  return {
    email: emailError(values.email.trim()),
    password: passwordError(values.password),
  };
}

export function validateSignup(values: SignupValues): SignupErrors {
  return {
    first_name: nameError(values.first_name, "First name"),
    last_name: nameError(values.last_name, "Last name"),
    email: emailError(values.email.trim()),
    password: passwordError(values.password),
    confirm_password: !values.confirm_password
      ? "Please confirm your password"
      : values.confirm_password !== values.password
        ? "Passwords do not match"
        : undefined,
  };
}
