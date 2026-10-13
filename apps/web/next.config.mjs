const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  // The API runs on a different domain (e.g. Render) than the web app (e.g.
  // Vercel). Proxying /api/* through this same origin means the browser
  // only ever talks to one domain, so the session cookie the API sets
  // actually lands here and is visible to middleware.ts and to every
  // subsequent fetch - a cookie set by a cross-site API response can't be
  // relied on otherwise (SameSite rules block it on fetch, and middleware
  // can never see a cookie scoped to a different registrable domain).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/:path*` }];
  },
};

export default nextConfig;
