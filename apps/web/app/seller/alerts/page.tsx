"use client";

import { Bell, PackageCheck, PackageX, Sparkles, TrendingDown, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  type AlertOut,
  type CurrentUser,
  formatRupees,
  getCurrentUser,
  listSellerAlerts,
} from "@/lib/api";

const NAV_LINKS = [
  { href: "/seller", label: "Groups" },
  { href: "/seller/alerts", label: "Alerts" },
  { href: "/seller/settings", label: "Alert settings" },
  { href: "/seller/billing", label: "Billing" },
];

const EVENT_META: Record<string, { icon: typeof Bell; tone: string }> = {
  price_drop: { icon: TrendingDown, tone: "bg-primary/10 text-primary" },
  price_rise: { icon: TrendingUp, tone: "bg-destructive/10 text-destructive" },
  out_of_stock: { icon: PackageX, tone: "bg-muted text-muted-foreground" },
  back_in_stock: { icon: PackageCheck, tone: "bg-primary/10 text-primary" },
  deal_start: { icon: Sparkles, tone: "bg-accent/10 text-accent" },
  deal_end: { icon: Sparkles, tone: "bg-muted text-muted-foreground" },
};

function describeChange(alert: AlertOut): string {
  if (alert.event_type === "price_drop" || alert.event_type === "price_rise") {
    const old = alert.old_value ? formatRupees(Number(alert.old_value)) : "?";
    const next = alert.new_value ? formatRupees(Number(alert.new_value)) : "?";
    return `${old} → ${next}`;
  }
  return alert.event_type?.replaceAll("_", " ") ?? "Change detected";
}

export default function SellerAlertsPage() {
  const [alerts, setAlerts] = useState<AlertOut[] | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    listSellerAlerts().then(setAlerts);
    getCurrentUser().then(setUser);
  }, []);

  return (
    <div className="min-h-screen">
      <AppHeader role="seller" email={user?.email} links={NAV_LINKS} />
      <main className="mx-auto max-w-2xl px-6 py-10">
        <h1 className="font-display mb-8 text-2xl tracking-tight">Alerts</h1>

        {alerts === null && (
          <div className="flex flex-col gap-4">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        )}

        {alerts?.length === 0 && (
          <EmptyState
            icon={Bell}
            title="No alerts yet"
            description="Once a tracked product's price, stock, or deal changes, you'll see it here."
          />
        )}

        <ol className="relative flex flex-col gap-1">
          {alerts?.map((alert, i) => {
            const meta = EVENT_META[alert.event_type ?? ""] ?? {
              icon: Bell,
              tone: "bg-muted text-muted-foreground",
            };
            const Icon = meta.icon;
            return (
              <li
                key={alert.id}
                className="animate-in-up relative flex gap-4 py-3"
                style={{ animationDelay: `${i * 40}ms` }}
              >
                {i < alerts.length - 1 && (
                  <span className="absolute left-[19px] top-11 h-[calc(100%-20px)] w-px bg-border" />
                )}
                <div
                  className={`flex size-10 shrink-0 items-center justify-center rounded-full ${meta.tone}`}
                >
                  <Icon className="size-4" />
                </div>
                <div className="flex min-w-0 flex-1 items-start justify-between gap-3 pt-1">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{alert.product_title ?? "Product"}</p>
                    <p className="text-sm text-muted-foreground">{describeChange(alert)}</p>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    <Badge variant={alert.status === "sent" ? "secondary" : "outline"}>
                      {alert.status}
                    </Badge>
                    {alert.sent_at && (
                      <span className="text-xs text-muted-foreground">
                        {new Date(alert.sent_at).toLocaleString("en-IN", {
                          day: "numeric",
                          month: "short",
                          hour: "numeric",
                          minute: "2-digit",
                        })}
                      </span>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </main>
    </div>
  );
}
