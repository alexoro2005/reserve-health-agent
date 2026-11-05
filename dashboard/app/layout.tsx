import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Reserve — Recovery Dashboard",
  description: "A readiness dashboard and AI agent built on ~1,000 days of Apple Watch data.",
};

// Applies the saved light/dark preference before the page paints (no flash)
const themeScript = `try{var t=localStorage.getItem("theme");if(t==="dark"||(!t&&matchMedia("(prefers-color-scheme: dark)").matches))document.documentElement.classList.add("dark")}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
        />
      </head>
      <body className="min-h-screen font-sans">{children}</body>
    </html>
  );
}
