"use client";

import { Heart, Search, Sparkles, X } from "lucide-react";
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
  type ProductCandidate,
  removeFromWishlist,
  smartTrack,
  type WishlistItem,
} from "@/lib/api";

const NAV_LINKS = [{ href: "/buyer", label: "Wishlist" }];

export default function BuyerDashboardPage() {
  const router = useRouter();
  const [wishlist, setWishlist] = useState<WishlistItem[] | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<ProductCandidate[] | null>(null);
  const [addingCandidate, setAddingCandidate] = useState<string | null>(null);

  useEffect(() => {
    listWishlist().then(setWishlist);
    getCurrentUser().then(setUser);
  }, []);

  async function handleRemove(event: React.MouseEvent, trackedItemId: string) {
    event.preventDefault();
    event.stopPropagation();
    setRemovingId(trackedItemId);
    try {
      await removeFromWishlist(trackedItemId);
      setWishlist((prev) => prev?.filter((w) => w.tracked_item_id !== trackedItemId) ?? null);
      toast.success("Removed from wishlist");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not remove that item.");
    } finally {
      setRemovingId(null);
    }
  }

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setCandidates(null);
    try {
      const result = await smartTrack(url);
      if (result.type === "direct_url") {
        const item = await addToWishlist(result.url);
        toast.success("Now tracking", { description: item.title ?? result.url });
        router.push(`/buyer/products/${item.product_id}`);
        return;
      }
      if (result.type === "candidates") {
        setCandidates(result.candidates);
        toast.success(`Found ${result.candidates.length} matching product(s)`, {
          description: "Pick the one you meant below.",
        });
        return;
      }
      if (result.type === "no_candidates") {
        toast.error("Couldn't find a matching product for that. Try a direct product link instead.");
        return;
      }
      toast.error(result.message);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not track that product.");
    } finally {
      setLoading(false);
    }
  }

  async function handlePickCandidate(candidate: ProductCandidate) {
    setAddingCandidate(candidate.url);
    try {
      const item = await addToWishlist(candidate.url);
      toast.success("Now tracking", { description: candidate.title });
      router.push(`/buyer/products/${item.product_id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not track that product.");
    } finally {
      setAddingCandidate(null);
    }
  }

  return (
    <div className="min-h-screen">
      <AppHeader role="buyer" email={user?.email} links={NAV_LINKS} />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="font-display mb-6 text-2xl tracking-tight">Your wishlist</h1>

        <form
          className="mb-2 flex flex-col gap-2 rounded-xl border bg-card p-2 sm:flex-row"
          onSubmit={handleAdd}
        >
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste a product link, a YouTube video, or describe what you want"
              className="border-0 pl-9 shadow-none focus-visible:ring-0"
            />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? "Looking..." : "Track it"}
          </Button>
        </form>
        <p className="mb-6 flex items-center gap-1.5 text-xs text-muted-foreground">
          <Sparkles className="size-3.5" />
          Works with Amazon.in, Flipkart or Meesho links, a YouTube review/comparison, or a plain
          description like &quot;budget wireless earbuds under 2000&quot;.
        </p>

        {candidates && candidates.length > 0 && (
          <div className="mb-8 rounded-xl border bg-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-medium">Which one did you mean?</h2>
              <button
                type="button"
                onClick={() => setCandidates(null)}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Dismiss
              </button>
            </div>
            <div className="flex flex-col gap-2">
              {candidates.map((candidate) => (
                <div
                  key={candidate.url}
                  className="flex items-center gap-3 rounded-lg border p-3"
                >
                  {candidate.image ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={candidate.image}
                      alt=""
                      className="size-12 shrink-0 rounded-md border object-cover"
                    />
                  ) : (
                    <div className="flex size-12 shrink-0 items-center justify-center rounded-md bg-secondary text-[10px] text-muted-foreground">
                      No image
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{candidate.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {candidate.marketplace.replace("_", ".")} ·{" "}
                      {formatRupees(candidate.price_paise)}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    disabled={addingCandidate === candidate.url}
                    onClick={() => handlePickCandidate(candidate)}
                  >
                    {addingCandidate === candidate.url ? "Adding..." : "Track this"}
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

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
              <Button
                variant="ghost"
                size="icon-sm"
                disabled={removingId === item.tracked_item_id}
                onClick={(e) => handleRemove(e, item.tracked_item_id)}
                aria-label="Remove from wishlist"
                className="shrink-0"
              >
                <X className="size-4" />
              </Button>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
