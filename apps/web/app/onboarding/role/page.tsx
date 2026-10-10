"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { setRole } from "@/lib/api";

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
    <main className="flex min-h-screen items-center justify-center px-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>What brings you to PriceWalk?</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Button size="lg" disabled={loading !== null} onClick={() => choose("seller")}>
            {loading === "seller" ? "Setting up..." : "I sell online"}
          </Button>
          <Button
            size="lg"
            variant="outline"
            disabled={loading !== null}
            onClick={() => choose("buyer")}
          >
            {loading === "buyer" ? "Setting up..." : "I shop online"}
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
