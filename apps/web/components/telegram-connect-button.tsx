"use client";

import { Send } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { createTelegramLinkToken } from "@/lib/api";

export function TelegramConnectButton() {
  const [deepLink, setDeepLink] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function connect() {
    setLoading(true);
    try {
      const { deep_link } = await createTelegramLinkToken();
      setDeepLink(deep_link);
      window.open(deep_link, "_blank");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not generate a Telegram link.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <Button type="button" variant="outline" disabled={loading} onClick={connect}>
        <Send className="size-4" />
        {loading ? "Generating link..." : "Connect Telegram for alerts"}
      </Button>
      {deepLink && (
        <p className="text-xs text-muted-foreground">
          If Telegram didn&apos;t open automatically,{" "}
          <a href={deepLink} className="link-underline" target="_blank" rel="noreferrer">
            tap here
          </a>{" "}
          and press Start.
        </p>
      )}
    </div>
  );
}
