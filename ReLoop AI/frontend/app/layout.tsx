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
    <html lang="en" className={`${inter.variable} scroll-smooth`}>
      <body className="min-h-screen flex flex-col font-sans antialiased bg-[#F5F5F7] text-[#1D1D1F] relative">
        <Providers>
          <BackgroundLightEffect />
          {children}
        </Providers>
      </body>
    </html>
  );
}
