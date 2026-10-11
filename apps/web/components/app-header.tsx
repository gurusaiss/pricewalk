"use client";

import { LogOut, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Logo } from "@/components/logo";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { logout } from "@/lib/api";

type NavLink = { href: string; label: string };

function initialsFor(email: string): string {
  return email.slice(0, 2).toUpperCase();
}

export function AppHeader({
  role,
  email,
  links,
}: {
  role: "seller" | "buyer";
  email?: string;
  links: NavLink[];
}) {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Logo href={`/${role}`} />
          <nav className="hidden items-center gap-1 sm:flex">
            {links.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    active ? "text-foreground" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {link.label}
                  {active && (
                    <span className="absolute inset-x-3 -bottom-[9px] h-0.5 rounded-full bg-primary" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="outline" className="hidden capitalize sm:inline-flex">
            {role}
          </Badge>
          <DropdownMenu>
            <DropdownMenuTrigger className="flex size-9 items-center justify-center rounded-full bg-secondary text-sm font-medium text-secondary-foreground transition-transform hover:scale-105 active:scale-95">
              {email ? initialsFor(email) : "?"}
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              {email && <div className="px-2 py-1.5 text-sm text-muted-foreground">{email}</div>}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/settings")}>
                <Settings className="size-4" /> Account settings
              </DropdownMenuItem>
              <DropdownMenuItem variant="destructive" onClick={handleLogout}>
                <LogOut className="size-4" /> Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <nav className="flex gap-4 overflow-x-auto border-t border-border/70 px-6 py-2 sm:hidden">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`whitespace-nowrap text-sm font-medium ${
              pathname === link.href ? "text-foreground" : "text-muted-foreground"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
