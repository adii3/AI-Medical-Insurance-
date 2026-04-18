import type { Metadata } from "next";

import { SessionProvider } from "@/components/providers/SessionProvider";

import "./globals.css";

export const metadata: Metadata = {
  title: "Medisight AI",
  description:
    "AI-powered medical insurance platform with secure onboarding, premium prediction, scenario planning, forecasting, and administrative analytics.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
