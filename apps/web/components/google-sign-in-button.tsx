"use client";

import Script from "next/script";
import { useEffect, useRef } from "react";

import { signInWithGoogle } from "@/lib/api";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          renderButton: (parent: HTMLElement, options: { width?: number }) => void;
        };
      };
    };
  }
}

export function GoogleSignInButton({ onSignedIn }: { onSignedIn: (role: string | null) => void }) {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  const buttonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!clientId || !window.google || !buttonRef.current) return;

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response) => {
        const user = await signInWithGoogle(response.credential);
        onSignedIn(user.role);
      },
    });
    window.google.accounts.id.renderButton(buttonRef.current, { width: 320 });
  }, [clientId, onSignedIn]);

  if (!clientId) {
    return null;
  }

  return (
    <>
      <Script src="https://accounts.google.com/gsi/client" strategy="afterInteractive" />
      <div ref={buttonRef} />
    </>
  );
}
