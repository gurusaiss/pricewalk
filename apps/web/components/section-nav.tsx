import Link from "next/link";

export function SectionNav({ links }: { links: { href: string; label: string }[] }) {
  return (
    <nav className="flex gap-4 border-b pb-3 text-sm">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className="text-muted-foreground hover:text-foreground"
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
