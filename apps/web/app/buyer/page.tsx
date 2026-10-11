"use client";

import { Heart, Link2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { AppHeader } from "@/components/app-header";
import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  addToWishlist,
  type CurrentUser,
  formatRupees,
  getCurrentUser,
  listWishlist,
  type WishlistItem,
} from "@/lib/api";

const NAV_LINKS = [{ href: "/buyer", label: "Wishlist" }];

export default function BuyerDashboardPage() {
  const router = useRouter();
  const [wishlist, setWishlist] = useState<WishlistItem[] | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listWishlist().then(setWishlist);
    getCurrentUser().then(setUser);
  }, []);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const item = await addToWishlist(url);
      router.push(`/buyer/products/${item.product_id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not track that product.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <AppHeader role="buyer" email={user?.email} links={NAV_LINKS} />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="font-display mb-6 text-2xl tracking-tight">Your wishlist</h1>

        <form
          className="mb-8 flex flex-col gap-2 rounded-xl border bg-card p-2 sm:flex-row"
          onSubmit={handleAdd}
        >
          <div className="relative flex-1">
            <Link2 className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste an Amazon.in, Flipkart or Meesho product link"
              className="border-0 pl-9 shadow-none focus-visible:ring-0"
            />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? "Adding..." : "Track it"}
          </Button>
        </form>

        {wishlist === null && (
          <div className="flex flex-col gap-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-20 w-full rounded-xl" />
            ))}
          </div>
        )}

        {wishlist?.length === 0 && (
          <EmptyState
            icon={Heart}
            title="Nothing tracked yet"
            description="Paste a product link above and we'll start watching its price."
          />
        )}

        <div className="flex flex-col gap-3">
          {wishlist?.map((item, i) => (
            <Link
              key={item.tracked_item_id}
              href={`/buyer/products/${item.product_id}`}
              className="card-hover animate-in-up flex items-center gap-4 rounded-xl border bg-card p-4"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              {item.image ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={item.image}
                  alt=""
                  className="size-14 shrink-0 rounded-lg border object-cover"
                />
              ) : (
                <div className="flex size-14 shrink-0 items-center justify-center rounded-lg bg-secondary text-xs text-muted-foreground">
                  No image
                </div>
              )}
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{item.title ?? item.url}</p>
                <p className="text-sm text-muted-foreground">
                  {formatRupees(item.current_price_paise)}
                  {item.target_price_paise !== null && (
                    <span className="text-xs">
                      {" "}
                      · target {formatRupees(item.target_price_paise)}
                    </span>
                  )}
                </p>
              </div>
              {item.in_stock === false && <Badge variant="destructive">Out of stock</Badge>}
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
