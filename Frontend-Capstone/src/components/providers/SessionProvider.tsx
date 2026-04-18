"use client";

import { createContext, useContext, useState, useSyncExternalStore } from "react";

import { clearSession, loadSession, saveSession } from "@/lib/session";
import type { AppSession, UserSummary } from "@/lib/types";

type SessionContextValue = {
  hydrated: boolean;
  session: AppSession | null;
  setSession: (session: AppSession | null) => void;
  updateUser: (user: UserSummary) => void;
};

const SessionContext = createContext<SessionContextValue | undefined>(undefined);
const emptySubscribe = () => () => {};

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [session, setSessionState] = useState<AppSession | null>(() => loadSession());
  const hydrated = useSyncExternalStore(emptySubscribe, () => true, () => false);

  const setSession = (nextSession: AppSession | null) => {
    setSessionState(nextSession);
    if (nextSession) {
      saveSession(nextSession);
    } else {
      clearSession();
    }
  };

  const updateUser = (user: UserSummary) => {
    setSessionState((current) => {
      if (!current) {
        return current;
      }
      const nextSession = { ...current, user };
      saveSession(nextSession);
      return nextSession;
    });
  };

  return (
    <SessionContext.Provider value={{ hydrated, session, setSession, updateUser }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const value = useContext(SessionContext);
  if (!value) {
    throw new Error("useSession must be used inside SessionProvider");
  }
  return value;
}
