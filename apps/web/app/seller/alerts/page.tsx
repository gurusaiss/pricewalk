"use client";

import { useEffect, useState } from "react";

import { SectionNav } from "@/components/section-nav";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { type AlertOut, formatRupees, listSellerAlerts } from "@/lib/api";

function describeChange(alert: AlertOut): string {
  if (alert.event_type === "price_drop" || alert.event_type === "price_rise") {
    const old = alert.old_value ? formatRupees(Number(alert.old_value)) : "?";
    const next = alert.new_value ? formatRupees(Number(alert.new_value)) : "?";
    return `${old} → ${next}`;
  }
  return alert.event_type?.replaceAll("_", " ") ?? "";
}

export default function SellerAlertsPage() {
  const [alerts, setAlerts] = useState<AlertOut[] | null>(null);

  useEffect(() => {
    listSellerAlerts().then(setAlerts);
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-6 flex flex-col gap-4">
        <h1 className="text-2xl font-semibold">Alerts</h1>
        <SectionNav
          links={[
            { href: "/seller", label: "Groups" },
            { href: "/seller/alerts", label: "Alerts" },
            { href: "/seller/settings", label: "Alert settings" },
            { href: "/settings", label: "Account" },
          ]}
        />
      </div>

      <div className="flex flex-col gap-3">
        {alerts?.length === 0 && <p className="text-sm text-muted-foreground">No alerts yet.</p>}
        {alerts?.map((alert) => (
          <Card key={alert.id}>
            <CardContent className="flex items-center justify-between py-4">
              <div>
                <p className="font-medium">{alert.product_title ?? "Product"}</p>
                <p className="text-sm text-muted-foreground">{describeChange(alert)}</p>
              </div>
              <div className="flex flex-col items-end gap-1">
                <Badge variant={alert.status === "sent" ? "secondary" : "outline"}>
                  {alert.status}
                </Badge>
                {alert.sent_at && (
                  <span className="text-xs text-muted-foreground">
                    {new Date(alert.sent_at).toLocaleString("en-IN")}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </main>
  );
}
