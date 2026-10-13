"use client";

import { ArrowRight, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { GoogleSignInButton } from "@/components/google-sign-in-button";
import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success("Signed in", { description: `Welcome back, ${user.email}.` });
      router.push(user.role ? `/${user.role}` : "/onboarding/role");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Invalid email or password.");
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
          <div className="border-b bg-secondary/40 px-6 py-5">
            <h1 className="font-display text-xl">Welcome back</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Sign in with your email and password.
            </p>
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
                    Sign in
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
          New here?{" "}
          <Link href="/signup" className="link-underline text-foreground">
            Create an account
          </Link>
        </p>
      </div>
    </main>
  );
}
