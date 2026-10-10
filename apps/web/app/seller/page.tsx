"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { SectionNav } from "@/components/section-nav";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createGroup, formatRupees, type Group, listGroups } from "@/lib/api";

const STATUS_VARIANT: Record<string, "default" | "destructive" | "secondary"> = {
  overpriced: "destructive",
  underpriced: "default",
  match: "secondary",
};

export default function SellerDashboardPage() {
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  function refresh() {
    listGroups().then(setGroups);
  }

  useEffect(refresh, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setCreating(true);
    try {
      await createGroup(name, url);
      setName("");
      setUrl("");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add that product.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-6 flex flex-col gap-4">
        <h1 className="text-2xl font-semibold">Seller dashboard</h1>
        <SectionNav
          links={[
            { href: "/seller", label: "Groups" },
            { href: "/seller/alerts", label: "Alerts" },
            { href: "/seller/settings", label: "Alert settings" },
            { href: "/settings", label: "Account" },
          ]}
        />
      </div>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Track a product</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={handleCreate}>
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="name">Group name</Label>
              <Input
                id="name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Wireless Mouse"
              />
            </div>
            <div className="flex flex-[2] flex-col gap-2">
              <Label htmlFor="url">Your product link</Label>
              <Input
                id="url"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.amazon.in/dp/..."
              />
            </div>
            <Button type="submit" disabled={creating}>
              {creating ? "Adding..." : "Add"}
            </Button>
          </form>
          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        {groups?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No groups yet - add your first product above.
          </p>
        )}
        {groups?.map((group) => {
          const own = group.members.find((m) => m.kind === "own");
          return (
            <Link key={group.id} href={`/seller/groups/${group.id}`}>
              <Card className="transition-colors hover:border-foreground/30">
                <CardHeader className="flex flex-row items-start justify-between gap-2">
                  <CardTitle className="text-base">{group.name}</CardTitle>
                  {group.status && (
                    <Badge variant={STATUS_VARIANT[group.status]}>
                      {group.status}
                      {group.gap_percent !== null ? ` ${Math.abs(group.gap_percent)}%` : ""}
                    </Badge>
                  )}
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground">
                  <p>Your price: {formatRupees(own?.current_price_paise)}</p>
                  <p>{group.members.length} tracked product(s)</p>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </main>
  );
}
