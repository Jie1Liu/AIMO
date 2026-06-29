import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIMO Backend Test",
  description: "Small test UI for the AIMO FastAPI backend"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
