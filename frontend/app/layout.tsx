import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuarryWatch | Quarry Monitoring",
  description: "Satellite-based unauthorized quarry expansion detection",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}