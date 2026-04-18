"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import LoadingState from "@/components/LoadingState";
import { getAuthenticatedHome } from "@/lib/constants";
import { useSession } from "@/components/providers/SessionProvider";

type RequireAuthProps = {
  children: React.ReactNode;
  role?: "user" | "admin";
};

export default function RequireAuth({ children, role }: RequireAuthProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { hydrated, session } = useSession();

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    if (!session) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    if (role && session.user.role !== role) {
      router.replace(getAuthenticatedHome(session));
    }
  }, [hydrated, pathname, role, router, session]);

  if (!hydrated || !session || (role && session.user.role !== role)) {
    return <LoadingState message="Preparing your account..." />;
  }

  return <>{children}</>;
}
