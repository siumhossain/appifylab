"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import type { LoginPayload } from "@/lib/api/auth";
import {
  validateLogin,
  validateSignup,
  type FieldErrors,
  type SignupValues,
} from "@/lib/validation/auth";
import { useAuthStore } from "@/store/auth";

function useAuthForm<T extends Record<string, string>>(
  initial: T,
  validate: (values: T) => FieldErrors<T>,
  submit: (values: T) => Promise<boolean>
) {
  const router = useRouter();
  const { loading, error, clearError } = useAuthStore();
  const [values, setValues] = useState<T>(initial);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors<T>>({});

  const setField = (name: keyof T) => (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setValues((v) => ({ ...v, [name]: value }));
    if (fieldErrors[name]) setFieldErrors((f) => ({ ...f, [name]: undefined }));
    if (error) clearError();
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (loading) return;
    const errors = validate(values);
    setFieldErrors(errors);
    if (Object.values(errors).some(Boolean)) return;
    if (await submit(values)) router.replace("/");
  };

  return {
    values,
    fieldErrors,
    serverError: error,
    submitting: loading,
    setField,
    handleSubmit,
  };
}

export function useLoginForm() {
  const login = useAuthStore((s) => s.login);
  return useAuthForm({ email: "", password: "" }, validateLogin, login);
}

export function useSignupForm() {
  const register = useAuthStore((s) => s.register);
  return useAuthForm<SignupValues>(
    { first_name: "", last_name: "", email: "", password: "", confirm_password: "" },
    validateSignup,
    ({ confirm_password: _, ...payload }) => register(payload)
  );
}
