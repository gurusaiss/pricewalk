import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center gap-10 px-6 py-20">
      <div className="flex flex-col items-center gap-4 text-center">
        <Badge variant="secondary">Built for Indian e-commerce</Badge>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">PriceWalk</h1>
        <p className="max-w-xl text-balance text-muted-foreground">
          Track competitor prices on Amazon.in, Flipkart and Meesho — or watch a product you want to
          buy — and get alerted the moment something changes.
        </p>
        <div className="flex gap-3">
          <Button>I sell online</Button>
          <Button variant="outline">I shop online</Button>
        </div>
      </div>

      <div className="grid w-full gap-6 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>For sellers</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Track competitor products and get alerts within minutes of a price change, stock-out, or
            new deal.
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>For buyers</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Paste a product link, set a target price, and get notified the moment it drops. Free,
            forever.
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
