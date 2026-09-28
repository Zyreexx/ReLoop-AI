import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/components/providers/Providers";
import { BackgroundLightEffect } from "@/components/ui/BackgroundLightEffect";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "ReLoop AI — The Next-Life Engine for Products",
  description:
    "ReLoop AI determines the highest-value next life for laptops and electronics: repair, upgrade, refurbishment, reuse, component recovery, or recycling.",
  keywords: [
    "Circular Economy",
    "Product Lifecycle",
    "Laptop Repair",
    "Hardware Diagnostics",
    "Next-Life Engine",
    "PCCoE Grand Challenge",
  ],
  authors: [{ name: "ReLoop AI Team" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth" className={`${inter.variable} scroll-smooth`} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var saved = localStorage.getItem('reloop_theme');
                  var pref = saved ? saved : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                  if (pref === 'dark') {
                    document.documentElement.classList.add('dark');
                    document.documentElement.setAttribute('data-theme', 'dark');
                  } else {
                    document.documentElement.classList.remove('dark');
                    document.documentElement.setAttribute('data-theme', 'light');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-screen flex flex-col font-sans antialiased bg-[#F5F5F7] dark:bg-[#000000] text-[#1D1D1F] dark:text-[#F5F5F7] relative">
        <Providers>
          <BackgroundLightEffect />
          {children}
        </Providers>
      </body>
    </html>
  );
}
