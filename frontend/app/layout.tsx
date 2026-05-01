import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "ReviewBot",
  description: "GitHub pull request review dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <nav className="border-b border-gray-800 bg-gray-900 px-6 py-3 flex items-center gap-8">
          <Link href="/" className="text-lg font-bold text-white flex items-center gap-2">
            <span className="text-blue-400">&#9670;</span> ReviewBot
          </Link>
          <Link href="/" className="text-sm text-gray-400 hover:text-white transition-colors">
            Pull Requests
          </Link>
          <Link href="/analytics" className="text-sm text-gray-400 hover:text-white transition-colors">
            Analytics
          </Link>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
