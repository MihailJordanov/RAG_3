import "../styles/globals.css";
import type { Metadata, Viewport } from "next";
import { GoogleOAuthProvider } from "@react-oauth/google";

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
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";

  return (
    <html lang="en">
      <body>
        <GoogleOAuthProvider clientId={clientId}>
          {children}
        </GoogleOAuthProvider>
      </body>
    </html>
  );
}