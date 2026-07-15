"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthShell, ErrorBanner, FieldError, PasswordInput, Spinner } from "@/components/auth/ui";
import { useLoginForm } from "@/hooks/use-auth-form";

export default function LoginPage() {
  const { values, fieldErrors, serverError, submitting, setField, handleSubmit } = useLoginForm();

  return (
    <AuthShell
      title="Welcome back"
      description="Sign in to your account to continue"
      footer={
        <>
          Don&apos;t have an account?
          <Link href="/signup" className="ml-1 font-medium text-foreground hover:underline">
            Sign up
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="grid gap-5">
        <ErrorBanner message={serverError} />

        <div className="grid gap-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={values.email}
            onChange={setField("email")}
            aria-invalid={!!fieldErrors.email}
            disabled={submitting}
          />
          <FieldError message={fieldErrors.email} />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="password">Password</Label>
          <PasswordInput
            id="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={values.password}
            onChange={setField("password")}
            aria-invalid={!!fieldErrors.password}
            disabled={submitting}
          />
          <FieldError message={fieldErrors.password} />
        </div>

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting && <Spinner />}
          {submitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthShell>
  );
}
