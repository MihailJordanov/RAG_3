import "../styles/globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "RAG Workspace",
  description: "Modern RAG chat interface",
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