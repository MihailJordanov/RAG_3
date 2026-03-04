import "../styles/globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "RAG Chat",
  description: "RAG Projects + Ingest + Chat",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}