"use client";

import { Check } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { AppHeader } from "@/components/app-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  type BillingInfo,
  type CurrentUser,
  formatRupees,
  getBilling,
  getCurrentUser,
  subscribeToPlan,
} from "@/lib/api";

const NAV_LINKS = [
  { href: "/seller", label: "Groups" },
  { href: "/seller/alerts", label: "Alerts" },
  { href: "/seller/settings", label: "Alert settings" },
  { href: "/seller/billing", label: "Billing" },
];

export default function SellerBillingPage() {
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [subscribing, setSubscribing] = useState<string | null>(null);

  useEffect(() => {
    getBilling().then(setBilling);
    getCurrentUser().then(setUser);
  }, []);

  async function handleSubscribe(planId: string) {
    setSubscribing(planId);
    try {
      const { checkout_url } = await subscribeToPlan(planId);
      if (checkout_url) {
        window.location.href = checkout_url;
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not start checkout.");
    } finally {
      setSubscribing(null);
    }
  }

  return (
    <div className="min-h-screen">
      <AppHeader role="seller" email={user?.email} links={NAV_LINKS} />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="font-display mb-8 text-2xl tracking-tight">Billing</h1>

        {!billing ? (
          <div className="grid gap-4 sm:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-64 rounded-2xl" />
            ))}
          </div>
        ) : (
          <>
            <div className="mb-8 rounded-xl border bg-card px-5 py-4">
              <p className="text-sm text-muted-foreground">Current plan</p>
              <p className="font-medium capitalize">
                {billing.current_plan}
                {billing.subscription_status && (
                  <span className="ml-2 font-normal capitalize text-muted-foreground">
                    {billing.subscription_status.replaceAll("_", " ")}
                    {billing.current_period_end &&
                      `, renews ${new Date(billing.current_period_end).toLocaleDateString("en-IN")}`}
                  </span>
                )}
              </p>
            </div>

            <div className="grid gap-5 sm:grid-cols-3">
              {billing.plans.map((plan) => {
                const isCurrent = plan.id === billing.current_plan;
                const isFeatured = plan.id === "starter";
                return (
                  <div
                    key={plan.id}
                    className={`flex flex-col gap-4 rounded-xl border p-6 ${
                      isFeatured ? "border-foreground/30" : ""
                    } ${isCurrent ? "bg-secondary/40" : "bg-card"}`}
                  >
                    <p className="font-medium">{plan.name}</p>
                    <p className="font-display text-3xl">
                      {plan.monthly_price_paise === 0 ? (
                        "Free"
                      ) : (
                        <>
                          {formatRupees(plan.monthly_price_paise)}
                          <span className="font-sans text-sm text-muted-foreground">/mo</span>
                        </>
                      )}
                    </p>
                    <ul className="flex flex-1 flex-col gap-2 text-sm text-muted-foreground">
                      <li className="flex items-center gap-2">
                        <Check className="size-4 text-primary" />
                        Up to {plan.competitor_limit} competitor products
                      </li>
                      <li className="flex items-center gap-2">
                        <Check className="size-4 text-primary" />
                        Checked every 15 minutes
                      </li>
                      <li className="flex items-center gap-2">
                        <Check className="size-4 text-primary" />
                        Telegram alerts
                      </li>
                    </ul>
                    {isCurrent ? (
                      <Badge variant="outline" className="w-fit">
                        Current plan
                      </Badge>
                    ) : plan.id !== "trial" ? (
                      <Button
                        variant={isFeatured ? "default" : "outline"}
                        disabled={subscribing === plan.id}
                        onClick={() => handleSubscribe(plan.id)}
                      >
                        {subscribing === plan.id ? "Starting checkout..." : "Upgrade"}
                      </Button>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
