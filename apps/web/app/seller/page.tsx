"use client";

import { ArrowUpRight, Boxes, Plus } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { AppHeader } from "@/components/app-header";
import { EmptyState } from "@/components/empty-state";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  createGroup,
  type CurrentUser,
  formatRupees,
  getCurrentUser,
  type Group,
  listGroups,
} from "@/lib/api";

const NAV_LINKS = [
  { href: "/seller", label: "Groups" },
  { href: "/seller/alerts", label: "Alerts" },
  { href: "/seller/settings", label: "Alert settings" },
  { href: "/seller/billing", label: "Billing" },
];

function StatusLabel({
  status,
  gapPercent,
}: {
  status: Group["status"];
  gapPercent: number | null;
}) {
  if (!status) return null;
  if (status === "match") {
    return <span className="text-xs text-muted-foreground">price-matched</span>;
  }
  const overpriced = status === "overpriced";
  return (
    <span className={`text-xs font-medium ${overpriced ? "text-destructive" : "text-primary"}`}>
      {overpriced ? "+" : "-"}
      {gapPercent !== null ? `${Math.abs(gapPercent)}%` : status}
    </span>
  );
}

function GroupCardSkeleton() {
  return (
    <div className="rounded-xl border bg-card p-5">
      <Skeleton className="h-5 w-2/3" />
      <Skeleton className="mt-3 h-4 w-1/3" />
      <Skeleton className="mt-4 h-4 w-1/2" />
    </div>
  );
}

export default function SellerDashboardPage() {
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [creating, setCreating] = useState(false);
  const [open, setOpen] = useState(false);

  function refresh() {
    listGroups().then(setGroups);
  }

  useEffect(() => {
    refresh();
    getCurrentUser().then(setUser);
  }, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setCreating(true);
    try {
      await createGroup(name, url);
      setName("");
      setUrl("");
      setOpen(false);
      refresh();
      toast.success("Product added", { description: `Now tracking "${name}".` });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not add that product.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen">
      <AppHeader role="seller" email={user?.email} links={NAV_LINKS} />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl tracking-tight">Your groups</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Each group pairs your product with the competitors you&apos;re watching.
            </p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger className={buttonVariants()}>
              <Plus className="size-4" /> Track a product
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Track a product</DialogTitle>
                <DialogDescription>
                  Paste a link to one of your own listings. You&apos;ll add competitors next.
                </DialogDescription>
              </DialogHeader>
              <form id="create-group" className="flex flex-col gap-4" onSubmit={handleCreate}>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="name">Group name</Label>
                  <Input
                    id="name"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Wireless Mouse"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="url">Your product link</Label>
                  <Input
                    id="url"
                    required
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://www.amazon.in/dp/..."
                  />
                </div>
              </form>
              <DialogFooter>
                <Button type="submit" form="create-group" disabled={creating}>
                  {creating ? "Adding..." : "Add"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {groups === null && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <GroupCardSkeleton key={i} />
            ))}
          </div>
        )}

        {groups?.length === 0 && (
          <EmptyState
            icon={Boxes}
            title="No groups yet"
            description="Add your first product to start comparing it against competitors."
            action={
              <Button onClick={() => setOpen(true)}>
                <Plus className="size-4" /> Track a product
              </Button>
            }
          />
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {groups?.map((group, i) => {
            const own = group.members.find((m) => m.kind === "own");
            return (
              <Link
                key={group.id}
                href={`/seller/groups/${group.id}`}
                className="card-hover animate-in-up group rounded-xl border bg-card p-5"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium">{group.name}</p>
                  <ArrowUpRight className="size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
                <p className="font-display mt-2 text-2xl">
                  {formatRupees(own?.current_price_paise)}
                </p>
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">
                    {group.members.length} product{group.members.length === 1 ? "" : "s"} tracked
                  </span>
                  <StatusLabel status={group.status} gapPercent={group.gap_percent} />
                </div>
              </Link>
            );
          })}
        </div>
      </main>
    </div>
  );
}
