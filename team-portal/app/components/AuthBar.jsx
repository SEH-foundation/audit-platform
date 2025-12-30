"use client";

import { signIn, signOut, useSession } from "next-auth/react";

export default function AuthBar() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return <div className="auth-status">Loading...</div>;
  }

  if (!session) {
    return (
      <button className="btn" onClick={() => signIn("google")}>
        Sign in with Google
      </button>
    );
  }

  return (
    <div className="auth-status">
      <span>{session.user?.email}</span>
      <button className="btn btn-secondary" onClick={() => signOut()}>
        Sign out
      </button>
    </div>
  );
}
