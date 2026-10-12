"use client";

import { Check } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { AppHeader } from "@/components/app-header";
import { TelegramConnectButton } from "@/components/telegram-connect-button";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  type AlertSettings,
  type CurrentUser,
  getAlertSettings,
  getCurrentUser,
  updateAlertSettings,
} from "@/lib/api";

const NAV_LINKS = [
  { href: "/seller", label: "Groups" },
  { href: "/seller/alerts", label: "Alerts" },
  { href: "/seller/settings", label: "Alert settings" },
  { href: "/seller/billing", label: "Billing" },
];

const EVENT_TYPES = [
  { value: "price_drop", label: "Price drop" },
  { value: "price_rise", label: "Price rise" },
  { value: "out_of_stock", label: "Out of stock" },
  { value: "back_in_stock", label: "Back in stock" },
  { value: "deal_start", label: "Deal starts" },
  { value: "deal_end", label: "Deal ends" },
];

export default function SellerAlertSettingsPage() {
  const [settings, setSettings] = useState<AlertSettings | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getAlertSettings().then(setSettings);
    getCurrentUser().then(setUser);
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
      toast.success("Settings saved");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not save settings.");
    } finally {
      setSaving(false);
    }
  }

  const allEventTypesEnabled = settings?.alert_event_types.length === 0;

  return (
    <div className="min-h-screen">
      <AppHeader role="seller" email={user?.email} links={NAV_LINKS} />
      <main className="mx-auto max-w-2xl px-6 py-10">
        <h1 className="font-display mb-8 text-2xl tracking-tight">Alert settings</h1>

        {!settings ? (
          <div className="flex flex-col gap-6">
            <Skeleton className="h-28 w-full rounded-xl" />
            <Skeleton className="h-40 w-full rounded-xl" />
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            <section className="rounded-xl border bg-card p-5">
              <h2 className="font-medium">Telegram</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Alerts come through as Telegram messages.
              </p>
              <div className="mt-4">
                <TelegramConnectButton />
              </div>
            </section>

            <section className="rounded-xl border bg-card p-5">
              <h2 className="font-medium">Which changes should alert you?</h2>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setSettings({ ...settings, alert_event_types: [] })}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
                    allEventTypesEnabled
                      ? "border-primary bg-primary text-primary-foreground"
                      : "hover:bg-secondary"
                  }`}
                >
                  {allEventTypesEnabled && <Check className="size-3.5" />}
                  All events
                </button>
                {EVENT_TYPES.map((type) => {
                  const active =
                    allEventTypesEnabled || settings.alert_event_types.includes(type.value);
                  return (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => toggleEventType(type.value)}
                      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
                        active ? "border-primary bg-primary/10 text-primary" : "hover:bg-secondary"
                      }`}
                    >
                      {active && <Check className="size-3.5" />}
                      {type.label}
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="rounded-xl border bg-card p-5">
              <h2 className="font-medium">Quiet hours (IST)</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Alerts during this window are held and delivered as one digest afterward.
              </p>
              <div className="mt-4 flex items-end gap-4">
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
                <p className="pb-2 text-xs text-muted-foreground">Leave blank to disable.</p>
              </div>
            </section>

            <Button onClick={save} disabled={saving} className="self-start">
              {saving ? "Saving..." : "Save settings"}
            </Button>
          </div>
        )}
      </main>
    </div>
  );
}
