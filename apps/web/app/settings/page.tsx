"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
      const updated = await setRole(nextRole);
      setUser(updated);
      window.location.href = `/${nextRole}`;
    } finally {
      setSwitching(false);
    }
  }

  if (!user) {
    return null;
  }

  return (
    <main className="mx-auto max-w-xl px-6 py-12">
      <Card>
        <CardHeader>
          <CardTitle>Account settings</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Email</p>
            <p>{user.email}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Current role</p>
            <Badge variant="secondary">{user.role ?? "not set"}</Badge>
          </div>
          {user.role && (
            <Button variant="outline" disabled={switching} onClick={switchRole}>
              {switching
                ? "Switching..."
                : `Switch to ${user.role === "seller" ? "buyer" : "seller"} mode`}
            </Button>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
