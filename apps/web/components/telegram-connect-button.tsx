"use client";

import { useState } from "react";

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
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <Button type="button" variant="outline" disabled={loading} onClick={connect}>
        {loading ? "Generating link..." : "Connect Telegram for alerts"}
      </Button>
      {deepLink && (
        <p className="text-xs text-muted-foreground">
          If Telegram didn&apos;t open automatically,{" "}
          <a href={deepLink} className="underline" target="_blank" rel="noreferrer">
            tap here
          </a>{" "}
          and press Start.
        </p>
      )}
    </div>
  );
}
