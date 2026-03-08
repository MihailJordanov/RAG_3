"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GoogleLogin } from "@react-oauth/google";

type Props = {
  open: boolean;
  onGuest: () => void | Promise<void>;
  onGoogleSuccess: (credential: string) => void | Promise<void>;
  onClose: () => void | Promise<void>;
  isLoading?: boolean;
  error?: string | null;
};

export default function AuthModal({
  open,
  onGuest,
  onGoogleSuccess,
  onClose,
  isLoading = false,
  error = null,
}: Props) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && open && !isLoading) {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, isLoading, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="auth-modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          <motion.div
            className="auth-modal-wrap"
            initial={{ opacity: 0, scale: 0.96, y: 18 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: 10 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
          >
            <div className="auth-modal-card">
              <button
                type="button"
                className="auth-close-btn"
                onClick={onClose}
                aria-label="Continue as guest"
                disabled={isLoading}
              >
                ×
              </button>

              <div className="auth-orb auth-orb-1" />
              <div className="auth-orb auth-orb-2" />

              <div className="auth-badge">Secure Workspace</div>

              <h2 className="auth-title glow-text">Welcome to RAG 3</h2>
              <p className="auth-subtitle">
                Sign in to keep your projects across sessions, or continue as a
                guest for a local device-only workspace.
              </p>

              <div className="auth-features">
                <div className="auth-feature-card">
                  <span className="auth-feature-dot" />
                  <div>
                    <div className="auth-feature-title">Google account</div>
                    <div className="auth-feature-text">
                      Sync your projects and chats more reliably.
                    </div>
                  </div>
                </div>

                <div className="auth-feature-card">
                  <span className="auth-feature-dot guest-dot" />
                  <div>
                    <div className="auth-feature-title">Guest mode</div>
                    <div className="auth-feature-text">
                      Stored only on this browser/device session history.
                    </div>
                  </div>
                </div>
              </div>

              <div className="auth-google-wrap">
                <GoogleLogin
                  onSuccess={(credentialResponse) => {
                    if (credentialResponse.credential) {
                      onGoogleSuccess(credentialResponse.credential);
                    }
                  }}
                  onError={() => {
                    console.error("Google login failed.");
                  }}
                  theme="outline"
                  size="large"
                  text="continue_with"
                  shape="pill"
                  width="320"
                />
              </div>

              <button
                type="button"
                className="guest-entry-btn"
                onClick={onGuest}
                disabled={isLoading}
              >
                {isLoading ? "Preparing session..." : "Continue as Guest"}
              </button>

              {error ? <div className="auth-error">{error}</div> : null}

              <p className="auth-footer-note">
                Closing this window will also continue as guest.
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}