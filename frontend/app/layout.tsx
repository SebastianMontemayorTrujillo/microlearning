import type { Metadata, Viewport } from "next";
import { Suspense } from "react";
import { LearningApp } from "@/components/app-shell";
import { Loading } from "@/components/ui";
import "katex/dist/katex.min.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lilt — A little wiser, every day",
  description:
    "Your personal microlearning space. Follow your curiosity through small lessons, thoughtful practice, and ideas that stay with you.",
  robots: { index: false, follow: false },
};
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#101310",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark">
      <body>
        <Suspense fallback={<Loading />}>
          <LearningApp />
        </Suspense>
        {children}
      </body>
    </html>
  );
}
