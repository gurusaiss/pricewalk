"use client";

import { ArrowLeftRight, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Logo } from "@/components/logo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { type CurrentUser, getCurrentUser, setRole } from "@/lib/api";

export default function SettingsPage() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function switchRole() {
    if (!user) return;
    setSwitching(true);
    try {
      const nextRole = user.role === "seller" ? "buyer" : "seller";
      await setRole(nextRole);
      toast.success(`Switched to ${nextRole} mode`);
      window.location.href = `/${nextRole}`;
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not switch role.");
      setSwitching(false);
    }
  }

  return (
    <main className="mx-auto max-w-xl px-6 py-12">
      <div className="mb-8 flex items-center justify-between">
        <Logo />
        {user?.role && (
          <Link
            href={`/${user.role}`}
            className="link-underline flex items-center gap-1.5 text-sm text-muted-foreground"
          >
            <ArrowLeft className="size-4" /> Back to dashboard
          </Link>
        )}
      </div>

      {!user ? (
        <Skeleton className="h-56 w-full rounded-2xl" />
      ) : (
        <div className="animate-in-up overflow-hidden rounded-2xl border bg-card">
          <div className="border-b px-6 py-5">
            <h1 className="font-display text-xl">Account settings</h1>
          </div>
          <div className="flex flex-col gap-5 px-6 py-6">
            <div>
              <p className="text-xs text-muted-foreground">Email</p>
              <p className="font-medium">{user.email}</p>
            </div>

            <div className="flex items-center justify-between rounded-xl border bg-secondary/30 p-4">
              <div>
                <p className="text-xs text-muted-foreground">Current mode</p>
                <Badge variant="secondary" className="mt-1 capitalize">
                  {user.role ?? "not set"}
                </Badge>
              </div>
              {user.role && (
                <Button variant="outline" disabled={switching} onClick={switchRole}>
                  <ArrowLeftRight className="size-4" />
                  {switching
                    ? "Switching..."
                    : `Switch to ${user.role === "seller" ? "buyer" : "seller"}`}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
