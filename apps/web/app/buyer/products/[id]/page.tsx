"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { PriceHistoryChart } from "@/components/price-history-chart";
import { TelegramConnectButton } from "@/components/telegram-connect-button";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  addToWishlist,
  buyLink,
  formatRupees,
  getProductDetail,
  type ProductDetail,
} from "@/lib/api";

export default function BuyerProductDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [targetRupees, setTargetRupees] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getProductDetail(params.id).then(setProduct);
  }, [params.id]);

  async function handleSetTarget(event: React.FormEvent) {
    event.preventDefault();
    if (!product) return;
    setSaving(true);
    setSaved(false);
    try {
      const paise = targetRupees ? Math.round(Number(targetRupees) * 100) : undefined;
      await addToWishlist(product.url, paise);
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  if (!product) return null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Button variant="ghost" className="mb-4" onClick={() => router.push("/buyer")}>
        ← Back to wishlist
      </Button>

      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{product.title ?? "Product"}</h1>
          <p className="text-sm capitalize text-muted-foreground">{product.marketplace}</p>
        </div>
        {product.in_stock === false && <Badge variant="destructive">Out of stock</Badge>}
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Current price</CardTitle>
          </CardHeader>
          <CardContent className="text-xl font-semibold">
            {formatRupees(product.current_price_paise)}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Lowest seen</CardTitle>
          </CardHeader>
          <CardContent className="text-xl font-semibold">
            {formatRupees(product.lowest_price_paise)}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Highest seen</CardTitle>
          </CardHeader>
          <CardContent className="text-xl font-semibold">
            {formatRupees(product.highest_price_paise)}
          </CardContent>
        </Card>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Price history</CardTitle>
        </CardHeader>
        <CardContent>
          <PriceHistoryChart
            series={[
              { id: product.id, label: product.title ?? "Price", points: product.price_history },
            ]}
          />
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Set target price</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex items-end gap-2" onSubmit={handleSetTarget}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="target">Alert me when price drops to (₹)</Label>
              <Input
                id="target"
                type="number"
                min={0}
                value={targetRupees}
                onChange={(e) => setTargetRupees(e.target.value)}
                placeholder="e.g. 999"
              />
            </div>
            <Button type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </Button>
          </form>
          {saved && <p className="mt-2 text-sm text-muted-foreground">Target price saved.</p>}
          <div className="mt-4">
            <TelegramConnectButton />
          </div>
        </CardContent>
      </Card>

      <a
        href={buyLink(product.id)}
        target="_blank"
        rel="noreferrer"
        className={buttonVariants({ size: "lg" })}
      >
        Buy on {product.marketplace.replace("_", ".")}
      </a>
    </main>
  );
}
