"use client";

import { ArrowLeft, Target, TrendingDown, TrendingUp } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { PriceHistoryChart } from "@/components/price-history-chart";
import { TelegramConnectButton } from "@/components/telegram-connect-button";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  addToWishlist,
  buyLink,
  formatRupees,
  getProductDetail,
  type ProductDetail,
} from "@/lib/api";

function StatTile({ label, value, tone }: { label: string; value: string; tone?: "down" | "up" }) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-display mt-1 flex items-center gap-1 text-xl">
        {tone === "down" && <TrendingDown className="size-4 text-primary" />}
        {tone === "up" && <TrendingUp className="size-4 text-destructive" />}
        {value}
      </p>
    </div>
  );
}

export default function BuyerProductDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [targetRupees, setTargetRupees] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getProductDetail(params.id).then(setProduct);
  }, [params.id]);

  async function handleSetTarget(event: React.FormEvent) {
    event.preventDefault();
    if (!product) return;
    setSaving(true);
    try {
      const paise = targetRupees ? Math.round(Number(targetRupees) * 100) : undefined;
      await addToWishlist(product.url, paise);
      toast.success("Target price saved", {
        description: "We'll alert you the moment it drops that low.",
      });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not save target price.");
    } finally {
      setSaving(false);
    }
  }

  if (!product) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <Skeleton className="h-8 w-48" />
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
        </div>
        <Skeleton className="mt-6 h-64 w-full rounded-xl" />
      </main>
    );
  }

  const atLowest =
    product.current_price_paise !== null &&
    product.lowest_price_paise !== null &&
    product.current_price_paise <= product.lowest_price_paise;

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <button
        onClick={() => router.push("/buyer")}
        className="link-underline mb-6 flex items-center gap-1.5 text-sm text-muted-foreground"
      >
        <ArrowLeft className="size-4" /> Back to wishlist
      </button>

      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl tracking-tight">{product.title ?? "Product"}</h1>
          <p className="mt-1 text-sm capitalize text-muted-foreground">
            {product.marketplace.replace("_", ".")}
          </p>
        </div>
        {product.in_stock === false && <Badge variant="destructive">Out of stock</Badge>}
      </div>

      {atLowest && (
        <div className="mb-6 flex items-center gap-2 rounded-lg bg-primary/10 px-4 py-2.5 text-sm text-primary">
          <TrendingDown className="size-4" /> This is the lowest price we&apos;ve seen since you
          started tracking.
        </div>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatTile label="Current price" value={formatRupees(product.current_price_paise)} />
        <StatTile
          label="Lowest seen"
          value={formatRupees(product.lowest_price_paise)}
          tone="down"
        />
        <StatTile
          label="Highest seen"
          value={formatRupees(product.highest_price_paise)}
          tone="up"
        />
      </div>

      <section className="mb-6 rounded-xl border bg-card p-5">
        <h2 className="mb-4 font-medium">Price history</h2>
        <PriceHistoryChart
          series={[
            { id: product.id, label: product.title ?? "Price", points: product.price_history },
          ]}
        />
      </section>

      <section className="mb-6 rounded-xl border bg-card p-5">
        <h2 className="flex items-center gap-2 font-medium">
          <Target className="size-4 text-muted-foreground" /> Set target price
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          We&apos;ll send a Telegram alert the instant the price drops to or below this.
        </p>
        <form className="mt-4 flex items-end gap-2" onSubmit={handleSetTarget}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="target">Target price (₹)</Label>
            <Input
              id="target"
              type="number"
              min={0}
              value={targetRupees}
              onChange={(e) => setTargetRupees(e.target.value)}
              placeholder="e.g. 999"
              className="w-40"
            />
          </div>
          <Button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </Button>
        </form>
        <div className="mt-4 border-t pt-4">
          <TelegramConnectButton />
        </div>
      </section>

      <a
        href={buyLink(product.id)}
        target="_blank"
        rel="noreferrer"
        className={buttonVariants({ size: "lg", className: "w-full sm:w-auto" })}
      >
        Buy on {product.marketplace.replace("_", ".")}
      </a>
    </main>
  );
}
