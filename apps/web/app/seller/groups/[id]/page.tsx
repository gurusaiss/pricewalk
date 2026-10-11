"use client";

import { ArrowLeft, Crown, ExternalLink, Package, Plus, Trash2 } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { PriceHistoryChart } from "@/components/price-history-chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  addCompetitor,
  formatRupees,
  getGroup,
  getGroupPriceHistory,
  type Group,
  type PriceHistorySeries,
  removeGroupItem,
} from "@/lib/api";

const STATUS_COPY: Record<string, string> = {
  overpriced: "priced above the cheapest competitor",
  underpriced: "priced below the cheapest competitor",
  match: "price-matched with the cheapest competitor",
};

export default function GroupDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [group, setGroup] = useState<Group | null>(null);
  const [history, setHistory] = useState<PriceHistorySeries[]>([]);
  const [competitorUrl, setCompetitorUrl] = useState("");
  const [adding, setAdding] = useState(false);

  function refresh() {
    getGroup(params.id).then(setGroup);
    getGroupPriceHistory(params.id).then(setHistory);
  }

  useEffect(refresh, [params.id]);

  async function handleAddCompetitor(event: React.FormEvent) {
    event.preventDefault();
    setAdding(true);
    try {
      await addCompetitor(params.id, competitorUrl);
      setCompetitorUrl("");
      refresh();
      toast.success("Competitor added");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not add that competitor.");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(trackedItemId: string) {
    await removeGroupItem(params.id, trackedItemId);
    refresh();
    toast("Removed from group");
  }

  if (!group) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-10">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="mt-6 h-64 w-full rounded-xl" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <button
        onClick={() => router.push("/seller")}
        className="link-underline mb-6 flex items-center gap-1.5 text-sm text-muted-foreground"
      >
        <ArrowLeft className="size-4" /> Back to groups
      </button>

      <div className="mb-8 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl tracking-tight">{group.name}</h1>
          {group.status && (
            <p className="mt-1 text-sm text-muted-foreground">
              {STATUS_COPY[group.status]}
              {group.gap_percent !== null && (
                <span
                  className={
                    group.status === "overpriced"
                      ? "font-medium text-destructive"
                      : "font-medium text-primary"
                  }
                >
                  {" "}
                  ({Math.abs(group.gap_percent)}%, {formatRupees(Math.abs(group.gap_paise ?? 0))})
                </span>
              )}
            </p>
          )}
        </div>
      </div>

      <section className="overflow-hidden rounded-xl border bg-card">
        <div className="border-b px-5 py-4">
          <h2 className="font-medium">Comparison</h2>
        </div>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>Kind</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Stock</TableHead>
                <TableHead>Deal</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {group.members.map((member) => (
                <TableRow key={member.tracked_item_id}>
                  <TableCell>
                    <a
                      href={member.url ?? "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="group inline-flex items-center gap-1.5 font-medium"
                    >
                      {member.title ?? member.product_id}
                      <ExternalLink className="size-3 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                    </a>
                    {member.is_cheapest && (
                      <Badge className="ml-2 gap-1 bg-primary/10 text-primary hover:bg-primary/10">
                        <Crown className="size-3" /> cheapest
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="capitalize text-muted-foreground">{member.kind}</TableCell>
                  <TableCell className="font-medium">
                    {formatRupees(member.current_price_paise)}
                  </TableCell>
                  <TableCell>
                    {member.in_stock === null ? (
                      "—"
                    ) : member.in_stock ? (
                      <span className="text-primary">In stock</span>
                    ) : (
                      <span className="text-destructive">Out of stock</span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {member.deal_label ?? "—"}
                  </TableCell>
                  <TableCell>
                    {member.kind === "competitor" && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => handleRemove(member.tracked_item_id)}
                        aria-label="Remove competitor"
                      >
                        <Trash2 className="size-4 text-muted-foreground" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <form className="flex gap-2 border-t bg-secondary/30 p-4" onSubmit={handleAddCompetitor}>
          <Input
            required
            value={competitorUrl}
            onChange={(e) => setCompetitorUrl(e.target.value)}
            placeholder="Add a competitor product link"
            className="bg-background"
          />
          <Button type="submit" disabled={adding}>
            <Plus className="size-4" /> {adding ? "Adding..." : "Add competitor"}
          </Button>
        </form>
      </section>

      <section className="mt-6 rounded-xl border bg-card p-5">
        <h2 className="mb-4 flex items-center gap-2 font-medium">
          <Package className="size-4 text-muted-foreground" /> Price history
        </h2>
        <PriceHistoryChart
          series={history.map((s) => ({
            id: s.product_id,
            label: `${s.title ?? s.product_id} (${s.kind})`,
            points: s.points,
          }))}
        />
      </section>
    </main>
  );
}
