export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CurrentUser = {
  id: string;
  email: string;
  role: "seller" | "buyer" | null;
  plan: string;
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail ?? `Request to ${path} failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function requestOtp(email: string) {
  return apiFetch<{ status: string }>("/auth/otp/request", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function verifyOtp(email: string, code: string) {
  return apiFetch<CurrentUser>("/auth/otp/verify", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
}

export function signInWithGoogle(idToken: string) {
  return apiFetch<CurrentUser>("/auth/google", {
    method: "POST",
    body: JSON.stringify({ id_token: idToken }),
  });
}

export function setRole(role: "seller" | "buyer") {
  return apiFetch<CurrentUser>("/auth/role", {
    method: "POST",
    body: JSON.stringify({ role }),
  });
}

export function getCurrentUser() {
  return apiFetch<CurrentUser>("/auth/me");
}

export function logout() {
  return apiFetch<{ status: string }>("/auth/logout", { method: "POST" });
}

export type PricePointOut = { ts: string; price_paise: number };

export type GroupMember = {
  tracked_item_id: string;
  product_id: string;
  kind: "own" | "competitor";
  title: string | null;
  url: string | null;
  marketplace: string | null;
  current_price_paise: number | null;
  mrp_paise: number | null;
  in_stock: boolean | null;
  deal_label: string | null;
  last_checked_at: string | null;
  is_cheapest: boolean;
};

export type Group = {
  id: string;
  name: string;
  members: GroupMember[];
  gap_paise: number | null;
  gap_percent: number | null;
  status: "overpriced" | "underpriced" | "match" | null;
};

export type PriceHistorySeries = {
  product_id: string;
  title: string | null;
  kind: string;
  points: PricePointOut[];
};

export type AlertOut = {
  id: string;
  channel: string;
  status: string;
  sent_at: string | null;
  event_type: string | null;
  old_value: string | null;
  new_value: string | null;
  product_title: string | null;
  product_url: string | null;
};

export type AlertSettings = {
  alert_channels: string[];
  alert_event_types: string[];
  quiet_hours_start: number | null;
  quiet_hours_end: number | null;
};

export function createGroup(name: string, productUrl: string) {
  return apiFetch<Group>("/seller/groups", {
    method: "POST",
    body: JSON.stringify({ name, product_url: productUrl }),
  });
}

export function listGroups() {
  return apiFetch<Group[]>("/seller/groups");
}

export function getGroup(groupId: string) {
  return apiFetch<Group>(`/seller/groups/${groupId}`);
}

export function addCompetitor(groupId: string, productUrl: string) {
  return apiFetch<Group>(`/seller/groups/${groupId}/competitors`, {
    method: "POST",
    body: JSON.stringify({ product_url: productUrl }),
  });
}

export function removeGroupItem(groupId: string, trackedItemId: string) {
  return apiFetch<{ status: string }>(`/seller/groups/${groupId}/items/${trackedItemId}`, {
    method: "DELETE",
  });
}

export function getGroupPriceHistory(groupId: string) {
  return apiFetch<PriceHistorySeries[]>(`/seller/groups/${groupId}/price-history`);
}

export function listSellerAlerts() {
  return apiFetch<AlertOut[]>("/seller/alerts");
}

export function getAlertSettings() {
  return apiFetch<AlertSettings>("/seller/alert-settings");
}

export function updateAlertSettings(update: Partial<AlertSettings>) {
  return apiFetch<AlertSettings>("/seller/alert-settings", {
    method: "PATCH",
    body: JSON.stringify(update),
  });
}

export type WishlistItem = {
  tracked_item_id: string;
  product_id: string;
  title: string | null;
  url: string | null;
  image: string | null;
  marketplace: string | null;
  current_price_paise: number | null;
  in_stock: boolean | null;
  lowest_price_paise: number | null;
  highest_price_paise: number | null;
  target_price_paise: number | null;
};

export type ProductDetail = {
  id: string;
  title: string | null;
  url: string;
  image: string | null;
  marketplace: string;
  current_price_paise: number | null;
  in_stock: boolean | null;
  lowest_price_paise: number | null;
  highest_price_paise: number | null;
  price_history: PricePointOut[];
};

export function addToWishlist(productUrl: string, targetPricePaise?: number) {
  return apiFetch<WishlistItem>("/buyer/wishlist", {
    method: "POST",
    body: JSON.stringify({ product_url: productUrl, target_price_paise: targetPricePaise ?? null }),
  });
}

export function listWishlist() {
  return apiFetch<WishlistItem[]>("/buyer/wishlist");
}

export function updateWishlistTarget(trackedItemId: string, targetPricePaise: number | null) {
  return apiFetch<WishlistItem>(`/buyer/wishlist/${trackedItemId}`, {
    method: "PATCH",
    body: JSON.stringify({ target_price_paise: targetPricePaise }),
  });
}

export function removeFromWishlist(trackedItemId: string) {
  return apiFetch<{ status: string }>(`/buyer/wishlist/${trackedItemId}`, { method: "DELETE" });
}

export function getProductDetail(productId: string) {
  return apiFetch<ProductDetail>(`/buyer/products/${productId}`);
}

export function buyLink(productId: string) {
  return `${API_URL}/redirect/buy/${productId}`;
}

export function createTelegramLinkToken() {
  return apiFetch<{ deep_link: string }>("/telegram/link-token", { method: "POST" });
}

export function formatRupees(paise: number | null | undefined): string {
  if (paise === null || paise === undefined) return "—";
  return `₹${(paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
}

export type PlanInfo = {
  id: string;
  name: string;
  monthly_price_paise: number;
  competitor_limit: number;
};

export type BillingInfo = {
  current_plan: string;
  subscription_status: string | null;
  current_period_end: string | null;
  plans: PlanInfo[];
};

export function getBilling() {
  return apiFetch<BillingInfo>("/seller/billing");
}

export function subscribeToPlan(plan: string) {
  return apiFetch<{ subscription_id: string; checkout_url: string | null }>(
    "/seller/billing/subscribe",
    { method: "POST", body: JSON.stringify({ plan }) },
  );
}
