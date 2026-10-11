"use client";

import { ArrowRight, Loader2, MailCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { GoogleSignInButton } from "@/components/google-sign-in-button";
import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { requestOtp, verifyOtp } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [step, setStep] = useState<"email" | "code">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleRequestOtp(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      await requestOtp(email);
      setStep("code");
      toast.success("Code sent", { description: `Check ${email} for a 6-digit code.` });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not send the code.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const user = await verifyOtp(email, code);
      router.push(user.role ? `/${user.role}` : "/onboarding/role");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Invalid or expired code.");
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
          <div className="border-b px-6 py-5">
            <h1 className="font-display text-xl">
              {step === "email" ? "Sign in" : "Check your inbox"}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {step === "email"
                ? "We'll email you a one-time code — no password to remember."
                : `We sent a 6-digit code to ${email}.`}
            </p>
          </div>

          <div className="px-6 py-6">
            {step === "email" ? (
              <form className="flex flex-col gap-4" onSubmit={handleRequestOtp}>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                  />
                </div>
                <Button type="submit" disabled={loading} className="group">
                  {loading ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <>
                      Send code
                      <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
                    </>
                  )}
                </Button>

                <div className="relative my-1 text-center text-xs text-muted-foreground">
                  <span className="relative z-10 bg-card px-2">or</span>
                  <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-border" />
                </div>

                <GoogleSignInButton
                  onSignedIn={(role) => router.push(role ? `/${role}` : "/onboarding/role")}
                />
              </form>
            ) : (
              <form className="flex flex-col gap-4" onSubmit={handleVerifyOtp}>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="code">6-digit code</Label>
                  <Input
                    id="code"
                    inputMode="numeric"
                    autoFocus
                    required
                    value={code}
                    onChange={(event) => setCode(event.target.value)}
                    placeholder="123456"
                    className="text-center text-lg tracking-[0.5em]"
                    maxLength={6}
                  />
                </div>
                <Button type="submit" disabled={loading}>
                  {loading ? <Loader2 className="size-4 animate-spin" /> : "Verify & continue"}
                </Button>
                <button
                  type="button"
                  className="link-underline mx-auto text-sm text-muted-foreground"
                  onClick={() => setStep("email")}
                >
                  Use a different email
                </button>
              </form>
            )}
          </div>
        </div>

        {step === "code" && (
          <p className="mt-4 flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
            <MailCheck className="size-3.5" /> Code expires in 5 minutes
          </p>
        )}
      </div>
    </main>
  );
}
