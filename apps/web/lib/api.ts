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
