"use client";

import { useEffect, useState } from "react";

import { SectionNav } from "@/components/section-nav";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type BillingInfo, formatRupees, getBilling, subscribeToPlan } from "@/lib/api";

export default function SellerBillingPage() {
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [subscribing, setSubscribing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBilling().then(setBilling);
  }, []);

  async function handleSubscribe(planId: string) {
    setSubscribing(planId);
    setError(null);
    try {
      const { checkout_url } = await subscribeToPlan(planId);
      if (checkout_url) {
        window.location.href = checkout_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start checkout.");
    } finally {
      setSubscribing(null);
    }
  }

  if (!billing) return null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-6 flex flex-col gap-4">
        <h1 className="text-2xl font-semibold">Billing</h1>
        <SectionNav
          links={[
            { href: "/seller", label: "Groups" },
            { href: "/seller/alerts", label: "Alerts" },
            { href: "/seller/settings", label: "Alert settings" },
            { href: "/seller/billing", label: "Billing" },
            { href: "/settings", label: "Account" },
          ]}
        />
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Current plan</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Badge variant="secondary" className="capitalize">
            {billing.current_plan}
          </Badge>
          {billing.subscription_status && (
            <span className="text-sm capitalize text-muted-foreground">
              {billing.subscription_status.replaceAll("_", " ")}
              {billing.current_period_end &&
                ` · renews ${new Date(billing.current_period_end).toLocaleDateString("en-IN")}`}
            </span>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-3">
        {billing.plans.map((plan) => (
          <Card
            key={plan.id}
            className={plan.id === billing.current_plan ? "border-foreground" : ""}
          >
            <CardHeader>
              <CardTitle>{plan.name}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <p className="text-2xl font-semibold">
                {plan.monthly_price_paise === 0
                  ? "Free"
                  : `${formatRupees(plan.monthly_price_paise)}/mo`}
              </p>
              <p className="text-sm text-muted-foreground">
                Up to {plan.competitor_limit} competitor products
              </p>
              {plan.id !== "trial" && plan.id !== billing.current_plan && (
                <Button disabled={subscribing === plan.id} onClick={() => handleSubscribe(plan.id)}>
                  {subscribing === plan.id ? "Starting checkout..." : "Upgrade"}
                </Button>
              )}
              {plan.id === billing.current_plan && (
                <Badge variant="outline" className="w-fit">
                  Current plan
                </Badge>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}
    </main>
  );
}
