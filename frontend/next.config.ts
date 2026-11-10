import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Cross-Origin-Opener-Policy",
            value: "same-origin-allow-popups",
          },
        ],
      },
    ];
  },
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
    return [
      {
        source: "/backend-api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/api/locator/:path*",
        destination: `${backendUrl}/api/locator/:path*`,
      },
      {
        source: "/api/batch/:path*",
        destination: `${backendUrl}/api/batch/:path*`,
      },
      {
        source: "/api/dpp/:path*",
        destination: `${backendUrl}/api/dpp/:path*`,
      },
    ];
  },
};

export default nextConfig;
