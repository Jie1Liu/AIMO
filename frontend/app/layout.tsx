import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIMO — Find the conversations that matter",
  description: "Live audience intelligence and human-reviewed outreach for Bluesky"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
