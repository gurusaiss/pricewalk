"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { PriceHistoryChart } from "@/components/price-history-chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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

const STATUS_VARIANT: Record<string, "default" | "destructive" | "secondary"> = {
  overpriced: "destructive",
  underpriced: "default",
  match: "secondary",
};

export default function GroupDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [group, setGroup] = useState<Group | null>(null);
  const [history, setHistory] = useState<PriceHistorySeries[]>([]);
  const [competitorUrl, setCompetitorUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  function refresh() {
    getGroup(params.id).then(setGroup);
    getGroupPriceHistory(params.id).then(setHistory);
  }

  useEffect(refresh, [params.id]);

  async function handleAddCompetitor(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setAdding(true);
    try {
      await addCompetitor(params.id, competitorUrl);
      setCompetitorUrl("");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add that competitor.");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(trackedItemId: string) {
    await removeGroupItem(params.id, trackedItemId);
    refresh();
  }

  if (!group) return null;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Button variant="ghost" className="mb-4" onClick={() => router.push("/seller")}>
        ← Back to groups
      </Button>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{group.name}</h1>
        {group.status && (
          <Badge variant={STATUS_VARIANT[group.status]}>
            {group.status} {group.gap_percent !== null ? `(${Math.abs(group.gap_percent)}%)` : ""}
          </Badge>
        )}
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Comparison</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>Kind</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Stock</TableHead>
                <TableHead>Deal</TableHead>
                <TableHead></TableHead>
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
                      className="hover:underline"
                    >
                      {member.title ?? member.product_id}
                    </a>
                    {member.is_cheapest && (
                      <Badge variant="secondary" className="ml-2">
                        cheapest
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="capitalize">{member.kind}</TableCell>
                  <TableCell>{formatRupees(member.current_price_paise)}</TableCell>
                  <TableCell>
                    {member.in_stock === null ? "—" : member.in_stock ? "In stock" : "Out of stock"}
                  </TableCell>
                  <TableCell>{member.deal_label ?? "—"}</TableCell>
                  <TableCell>
                    {member.kind === "competitor" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemove(member.tracked_item_id)}
                      >
                        Remove
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <form className="mt-4 flex gap-2" onSubmit={handleAddCompetitor}>
            <Input
              required
              value={competitorUrl}
              onChange={(e) => setCompetitorUrl(e.target.value)}
              placeholder="Add a competitor product link"
            />
            <Button type="submit" disabled={adding}>
              {adding ? "Adding..." : "Add competitor"}
            </Button>
          </form>
          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Price history</CardTitle>
        </CardHeader>
        <CardContent>
          <PriceHistoryChart
            series={history.map((s) => ({
              id: s.product_id,
              label: `${s.title ?? s.product_id} (${s.kind})`,
              points: s.points,
            }))}
          />
        </CardContent>
      </Card>
    </main>
  );
}
