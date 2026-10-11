import { Bell, LineChart, Link2, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { Logo } from "@/components/logo";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";

const STEPS = [
  {
    icon: Link2,
    title: "Paste a link",
    body: "Drop in any Amazon.in, Flipkart or Meesho product URL — yours, or one you want to buy.",
  },
  {
    icon: LineChart,
    title: "We watch it for you",
    body: "Checked every 15–60 minutes. Price, stock, and deal badges, tracked from the moment you add it.",
  },
  {
    icon: Bell,
    title: "Get alerted instantly",
    body: "A Telegram message the moment something moves — no refreshing tabs, no missed drops.",
  },
];

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <Logo />
        <Link href="/login" className="link-underline text-sm font-medium">
          Sign in
        </Link>
      </header>

      {/* Hero */}
      <section className="mx-auto grid w-full max-w-6xl flex-1 items-center gap-16 px-6 py-12 lg:grid-cols-[1.1fr_1fr] lg:py-20">
        <div className="animate-in-up flex flex-col items-start gap-6">
          <Badge variant="secondary" className="gap-1.5">
            <ShieldCheck className="size-3.5" /> Built for Indian e-commerce
          </Badge>
          <h1 className="font-display text-5xl leading-[1.05] tracking-tight sm:text-6xl">
            Know the moment
            <br />a price <span className="text-primary">moves</span>.
          </h1>
          <p className="max-w-md text-balance text-lg text-muted-foreground">
            Track competitor prices on Amazon.in, Flipkart and Meesho — or watch something you want
            to buy — and hear about it before anyone else does.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/login" className={buttonVariants({ size: "lg" })}>
              I sell online
            </Link>
            <Link href="/login" className={buttonVariants({ size: "lg", variant: "outline" })}>
              I shop online
            </Link>
          </div>
          <p className="text-xs text-muted-foreground">
            Free to start. No card required for buyers, ever.
          </p>
        </div>

        {/* Illustrative product mockup */}
        <div className="animate-in-up relative [animation-delay:150ms]">
          <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-primary/5" />
          <div className="overflow-hidden rounded-2xl border bg-card shadow-xl shadow-foreground/5">
            <div className="flex items-center justify-between border-b px-5 py-3.5">
              <span className="text-sm font-medium">Wireless Earbuds Pro</span>
              <Badge className="bg-destructive/10 text-destructive hover:bg-destructive/10">
                9.2% overpriced
              </Badge>
            </div>
            <div className="divide-y">
              <div className="flex items-center justify-between px-5 py-3.5">
                <span className="text-sm text-muted-foreground">Your price</span>
                <span className="font-display text-lg">₹2,199</span>
              </div>
              <div className="flex items-center justify-between bg-primary/5 px-5 py-3.5">
                <span className="text-sm text-muted-foreground">Cheapest competitor</span>
                <span className="font-display text-lg text-primary">₹2,013</span>
              </div>
            </div>
            <div className="flex items-center gap-2 border-t bg-secondary/50 px-5 py-3 text-xs text-muted-foreground">
              <Bell className="size-3.5 text-accent" />
              Alert sent 2 min ago via Telegram
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t bg-secondary/30 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl tracking-tight sm:text-3xl">How it works</h2>
          <div className="mt-10 grid gap-8 sm:grid-cols-3">
            {STEPS.map((step, i) => (
              <div
                key={step.title}
                className="animate-in-up"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <step.icon className="size-5" />
                </div>
                <h3 className="mt-4 font-medium">{step.title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Audience split */}
      <section className="mx-auto w-full max-w-6xl px-6 py-20">
        <div className="grid gap-6 sm:grid-cols-2">
          <div className="card-hover rounded-2xl border bg-card p-8">
            <p className="text-sm font-medium text-primary">For sellers</p>
            <h3 className="font-display mt-2 text-2xl">Never get undercut quietly.</h3>
            <p className="mt-3 text-sm text-muted-foreground">
              Group your product with its competitors, see who&apos;s cheapest at a glance, and get
              alerted within minutes of a price change, stock-out, or new deal.
            </p>
          </div>
          <div className="card-hover rounded-2xl border bg-card p-8">
            <p className="text-sm font-medium text-accent">For buyers</p>
            <h3 className="font-display mt-2 text-2xl">Buy at the right moment.</h3>
            <p className="mt-3 text-sm text-muted-foreground">
              Paste a product link, set a target price, and get notified the instant it drops. Free,
              forever — no catch.
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t px-6 py-8 text-center text-xs text-muted-foreground">
        PriceWalk — price tracking for Indian e-commerce.
      </footer>
    </div>
  );
}
