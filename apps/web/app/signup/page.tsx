"use client";

import { ArrowRight, Check, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { GoogleSignInButton } from "@/components/google-sign-in-button";
import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { register } from "@/lib/api";

const BENEFITS = [
  "Track competitor prices or a wishlist, free to start",
  "Telegram alerts the moment something changes",
  "No card needed to create an account",
];

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      await register(email, password);
      toast.success("Account created", {
        description: "Sign in with your new email and password to continue.",
      });
      router.push("/login");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not create your account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="animate-in-up w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Logo />
        </div>

        <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
          <div className="border-b bg-primary/5 px-6 py-5">
            <h1 className="font-display text-xl">Create your account</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Pick a password with at least 8 characters.
            </p>
            <ul className="mt-4 flex flex-col gap-1.5">
              {BENEFITS.map((benefit) => (
                <li key={benefit} className="flex items-start gap-2 text-xs text-muted-foreground">
                  <Check className="mt-0.5 size-3.5 shrink-0 text-primary" />
                  {benefit}
                </li>
              ))}
            </ul>
          </div>

          <div className="px-6 py-6">
            <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
              <div className="flex flex-col gap-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  required
                  autoFocus
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                />
              </div>
              <Button type="submit" disabled={loading} className="group">
                {loading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <>
                    Create account
                    <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
                  </>
                )}
              </Button>

              <div className="relative my-1 text-center text-xs text-muted-foreground">
                <span className="relative z-10 bg-card px-2">or</span>
                <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-border" />
              </div>

              <GoogleSignInButton
                onSignedIn={(role) => {
                  toast.success("Signed in with Google");
                  router.push(role ? `/${role}` : "/onboarding/role");
                }}
              />
            </form>
          </div>
        </div>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="link-underline text-foreground">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
