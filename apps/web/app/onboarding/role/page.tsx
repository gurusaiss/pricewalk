"use client";

import { Loader2, ShoppingBag, Store } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Logo } from "@/components/logo";
import { setRole } from "@/lib/api";

const OPTIONS = [
  {
    role: "seller" as const,
    icon: Store,
    title: "I sell online",
    body: "Track competitor prices on your listings and know the moment someone undercuts you.",
  },
  {
    role: "buyer" as const,
    icon: ShoppingBag,
    title: "I shop online",
    body: "Watch a product you want, set a target price, and get notified the moment it drops.",
  },
];

export default function RolePickerPage() {
  const router = useRouter();
  const [loading, setLoading] = useState<"seller" | "buyer" | null>(null);

  async function choose(role: "seller" | "buyer") {
    setLoading(role);
    try {
      await setRole(role);
      router.push(`/${role}`);
    } finally {
      setLoading(null);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-10 px-6 py-12">
      <Logo />
      <div className="animate-in-up text-center">
        <h1 className="font-display text-3xl tracking-tight">What brings you here?</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          This sets up your dashboard — you can switch later from settings.
        </p>
      </div>

      <div className="grid w-full max-w-2xl gap-4 sm:grid-cols-2">
        {OPTIONS.map((option, i) => (
          <button
            key={option.role}
            type="button"
            disabled={loading !== null}
            onClick={() => choose(option.role)}
            style={{ animationDelay: `${i * 80}ms` }}
            className="card-hover animate-in-up group flex flex-col items-start gap-3 rounded-2xl border bg-card p-6 text-left disabled:opacity-60"
          >
            <div className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
              {loading === option.role ? (
                <Loader2 className="size-5 animate-spin" />
              ) : (
                <option.icon className="size-5" />
              )}
            </div>
            <p className="font-display text-lg">{option.title}</p>
            <p className="text-sm text-muted-foreground">{option.body}</p>
          </button>
        ))}
      </div>
    </main>
  );
}
