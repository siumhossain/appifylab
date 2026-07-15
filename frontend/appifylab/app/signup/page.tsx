"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthShell, ErrorBanner, FieldError, PasswordInput, Spinner } from "@/components/auth/ui";
import { useSignupForm } from "@/hooks/use-auth-form";

export default function SignupPage() {
  const { values, fieldErrors, serverError, submitting, setField, handleSubmit } = useSignupForm();

  return (
    <AuthShell
      title="Create your account"
      description="Start sharing in a few seconds"
      footer={
        <>
          Already have an account?
          <Link href="/login" className="ml-1 font-medium text-foreground hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="grid gap-5">
        <ErrorBanner message={serverError} />

        <div className="grid grid-cols-2 gap-3">
          <div className="grid gap-2">
            <Label htmlFor="first_name">First name</Label>
            <Input
              id="first_name"
              autoComplete="given-name"
              placeholder="John"
              value={values.first_name}
              onChange={setField("first_name")}
              aria-invalid={!!fieldErrors.first_name}
              disabled={submitting}
            />
            <FieldError message={fieldErrors.first_name} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="last_name">Last name</Label>
            <Input
              id="last_name"
              autoComplete="family-name"
              placeholder="Doe"
              value={values.last_name}
              onChange={setField("last_name")}
              aria-invalid={!!fieldErrors.last_name}
              disabled={submitting}
            />
            <FieldError message={fieldErrors.last_name} />
          </div>
        </div>

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
            autoComplete="new-password"
            placeholder="At least 8 characters"
            value={values.password}
            onChange={setField("password")}
            aria-invalid={!!fieldErrors.password}
            disabled={submitting}
          />
          <FieldError message={fieldErrors.password} />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="confirm_password">Confirm password</Label>
          <PasswordInput
            id="confirm_password"
            autoComplete="new-password"
            placeholder="Repeat your password"
            value={values.confirm_password}
            onChange={setField("confirm_password")}
            aria-invalid={!!fieldErrors.confirm_password}
            disabled={submitting}
          />
          <FieldError message={fieldErrors.confirm_password} />
        </div>

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting && <Spinner />}
          {submitting ? "Creating account…" : "Create account"}
        </Button>
      </form>
    </AuthShell>
  );
}
