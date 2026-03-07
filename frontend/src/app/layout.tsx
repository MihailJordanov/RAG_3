import "../styles/globals.css";
import type { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "RAG Workspace",
  description: "Modern RAG chat interface",
};

export const viewport: Viewport = {
  themeColor: "#06060a",
  colorScheme: "dark",
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