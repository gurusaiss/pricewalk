import Link from "next/link";

import { Logo } from "@/components/logo";
import { buttonVariants } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-6">
        <Logo />
        <Link href="/login" className="link-underline text-sm font-medium">
          Sign in
        </Link>
      </header>

      <section className="mx-auto w-full max-w-5xl px-6 pb-16 pt-8">
        <h1 className="font-display max-w-2xl text-4xl leading-tight tracking-tight sm:text-5xl">
          Price tracking for Amazon.in, Flipkart and Meesho.
        </h1>
        <p className="mt-5 max-w-xl text-lg text-muted-foreground">
          If you sell online, PriceWalk watches your competitors and tells you when they change
          price. If you&apos;re buying something, it watches the listing and tells you when the
          price drops. Either way, you find out on Telegram, not by checking a tab fifty times a
          day.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link href="/login" className={buttonVariants({ size: "lg" })}>
            I sell online
          </Link>
          <Link href="/login" className={buttonVariants({ size: "lg", variant: "outline" })}>
            I&apos;m buying something
          </Link>
        </div>
      </section>

      <section className="border-y bg-secondary/40 px-6 py-14">
        <div className="mx-auto max-w-5xl">
          <p className="text-sm text-muted-foreground">An example of what a seller sees:</p>
          <div className="mt-4 max-w-md overflow-hidden rounded-lg border bg-card">
            <div className="flex items-center justify-between border-b px-4 py-3">
              <span className="text-sm font-medium">Wireless Earbuds Pro</span>
              <span className="text-sm text-destructive">9.2% above competitor</span>
            </div>
            <div className="divide-y text-sm">
              <div className="flex items-center justify-between px-4 py-2.5">
                <span className="text-muted-foreground">Your price</span>
                <span>₹2,199</span>
              </div>
              <div className="flex items-center justify-between px-4 py-2.5">
                <span className="text-muted-foreground">Cheapest competitor</span>
                <span>₹2,013</span>
              </div>
            </div>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            A Telegram message goes out the moment that gap changes.
          </p>
        </div>
      </section>

      <section className="mx-auto w-full max-w-5xl px-6 py-14">
        <div className="grid gap-10 sm:grid-cols-2">
          <div>
            <h2 className="font-display text-xl">For sellers</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Add your product and the competitors you want to watch. You&apos;ll see a table of
              who&apos;s cheapest, and get a message when someone undercuts you, runs a deal, or
              goes out of stock. The free plan covers 10 competitor products.
            </p>
          </div>
          <div>
            <h2 className="font-display text-xl">For buyers</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Paste a link to something you want and set a price you&apos;re willing to pay. We
              check it every hour and message you the moment it drops to or below that. No limit, no
              cost.
            </p>
          </div>
        </div>
      </section>

      <footer className="mt-auto border-t px-6 py-6 text-sm text-muted-foreground">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <span>PriceWalk</span>
          <span>Amazon.in, Flipkart, Meesho</span>
        </div>
      </footer>
    </div>
  );
}
