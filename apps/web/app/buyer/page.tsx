"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { addToWishlist, formatRupees, listWishlist, type WishlistItem } from "@/lib/api";

export default function BuyerDashboardPage() {
  const router = useRouter();
  const [wishlist, setWishlist] = useState<WishlistItem[] | null>(null);
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listWishlist().then(setWishlist);
  }, []);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const item = await addToWishlist(url);
      router.push(`/buyer/products/${item.product_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not track that product.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="mb-6 text-2xl font-semibold">Your wishlist</h1>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Track a product</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex gap-2" onSubmit={handleAdd}>
            <Input
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste an Amazon.in, Flipkart or Meesho product link"
            />
            <Button type="submit" disabled={loading}>
              {loading ? "Adding..." : "Track"}
            </Button>
          </form>
          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      <div className="flex flex-col gap-3">
        {wishlist?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Nothing tracked yet - paste a product link above.
          </p>
        )}
        {wishlist?.map((item) => (
          <Link key={item.tracked_item_id} href={`/buyer/products/${item.product_id}`}>
            <Card className="transition-colors hover:border-foreground/30">
              <CardContent className="flex items-center justify-between py-4">
                <div>
                  <p className="font-medium">{item.title ?? item.url}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatRupees(item.current_price_paise)}
                    {item.target_price_paise !== null &&
                      ` · target ${formatRupees(item.target_price_paise)}`}
                  </p>
                </div>
                {item.in_stock === false && <Badge variant="destructive">Out of stock</Badge>}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </main>
  );
}
