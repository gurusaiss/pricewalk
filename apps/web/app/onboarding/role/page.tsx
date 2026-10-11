"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Logo } from "@/components/logo";
import { setRole } from "@/lib/api";

const OPTIONS = [
  {
    role: "seller" as const,
    title: "I sell online",
    body: "Track competitor prices on your listings and know when someone undercuts you.",
  },
  {
    role: "buyer" as const,
    title: "I'm buying something",
    body: "Watch a product, set a price you want to pay, and get told when it drops.",
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
      <div className="text-center">
        <h1 className="font-display text-2xl tracking-tight">Which one are you?</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          You can switch this later from settings.
        </p>
      </div>

      <div className="grid w-full max-w-xl gap-3 sm:grid-cols-2">
        {OPTIONS.map((option) => (
          <button
            key={option.role}
            type="button"
            disabled={loading !== null}
            onClick={() => choose(option.role)}
            className="flex flex-col items-start gap-1.5 rounded-lg border bg-card p-5 text-left transition-colors hover:border-foreground/30 disabled:opacity-60"
          >
            <p className="font-medium">
              {loading === option.role ? "Setting up..." : option.title}
            </p>
            <p className="text-sm text-muted-foreground">{option.body}</p>
          </button>
        ))}
      </div>
    </main>
  );
}
