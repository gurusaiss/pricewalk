import Link from "next/link";

export function Logo({ href = "/", className = "" }: { href?: string; className?: string }) {
  return (
    <Link href={href} className={`group flex items-center gap-2 ${className}`}>
      <svg
        width="26"
        height="26"
        viewBox="0 0 26 26"
        fill="none"
        className="shrink-0"
        aria-hidden="true"
      >
        <rect width="26" height="26" rx="7" className="fill-primary" />
        <path
          d="M5.5 16.5L9.5 11.5L13 14.5L20.5 6"
          stroke="hsl(var(--primary-foreground))"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        <path
          d="M16 6H20.5V10.5"
          stroke="hsl(var(--primary-foreground))"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </svg>
      <span className="font-display text-lg font-medium tracking-tight transition-colors group-hover:text-primary">
        PriceWalk
      </span>
    </Link>
  );
}
