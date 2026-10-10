"use client";

import { useEffect, useState } from "react";

import { SectionNav } from "@/components/section-nav";
import { TelegramConnectButton } from "@/components/telegram-connect-button";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { type AlertSettings, getAlertSettings, updateAlertSettings } from "@/lib/api";

const EVENT_TYPES = [
  "price_drop",
  "price_rise",
  "out_of_stock",
  "back_in_stock",
  "deal_start",
  "deal_end",
];

export default function SellerAlertSettingsPage() {
  const [settings, setSettings] = useState<AlertSettings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getAlertSettings().then(setSettings);
  }, []);

  function toggleEventType(type: string) {
    if (!settings) return;
    const enabled = settings.alert_event_types.includes(type);
    const next = enabled
      ? settings.alert_event_types.filter((t) => t !== type)
      : [...settings.alert_event_types, type];
    setSettings({ ...settings, alert_event_types: next });
  }

  async function save() {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await updateAlertSettings(settings);
      setSettings(updated);
    } finally {
      setSaving(false);
    }
  }

  if (!settings) return null;

  const allEventTypesEnabled = settings.alert_event_types.length === 0;

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <div className="mb-6 flex flex-col gap-4">
        <h1 className="text-2xl font-semibold">Alert settings</h1>
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
          <CardTitle>Telegram</CardTitle>
        </CardHeader>
        <CardContent>
          <TelegramConnectButton />
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Which changes should alert you?</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={allEventTypesEnabled}
              onChange={() => setSettings({ ...settings, alert_event_types: [] })}
            />
            All event types
          </label>
          {EVENT_TYPES.map((type) => (
            <label key={type} className="flex items-center gap-2 text-sm capitalize">
              <input
                type="checkbox"
                disabled={allEventTypesEnabled}
                checked={allEventTypesEnabled || settings.alert_event_types.includes(type)}
                onChange={() => toggleEventType(type)}
              />
              {type.replaceAll("_", " ")}
            </label>
          ))}
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Quiet hours (IST)</CardTitle>
        </CardHeader>
        <CardContent className="flex items-end gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="quiet-start">From</Label>
            <Input
              id="quiet-start"
              type="number"
              min={0}
              max={23}
              value={settings.quiet_hours_start ?? ""}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  quiet_hours_start: e.target.value === "" ? null : Number(e.target.value),
                })
              }
              className="w-20"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="quiet-end">To</Label>
            <Input
              id="quiet-end"
              type="number"
              min={0}
              max={23}
              value={settings.quiet_hours_end ?? ""}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  quiet_hours_end: e.target.value === "" ? null : Number(e.target.value),
                })
              }
              className="w-20"
            />
          </div>
          <p className="text-xs text-muted-foreground">Leave blank to disable quiet hours.</p>
        </CardContent>
      </Card>

      <Button onClick={save} disabled={saving}>
        {saving ? "Saving..." : "Save settings"}
      </Button>
    </main>
  );
}
