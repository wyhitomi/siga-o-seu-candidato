"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useRef, useState } from "react";
import { setToken } from "@/lib/admin-session";
import { api } from "@/lib/api/client";

export default function VerifyPage({ searchParams }: PageProps<"/admin/verificar">) {
  const raw = use(searchParams).token;
  const token = Array.isArray(raw) ? raw[0] : raw;
  const router = useRouter();
  const [requestFailed, setRequestFailed] = useState(false);
  const started = useRef(false);
  const failed = !token || requestFailed;

  useEffect(() => {
    // The link is single-use: guard against React running the effect twice.
    if (!token || started.current) return;
    started.current = true;
    api
      .POST("/api/v1/auth/verify", { body: { token } })
      .then(({ data }) => {
        if (!data) return setRequestFailed(true);
        setToken(data.access_token);
        router.replace("/admin");
      })
      .catch(() => setRequestFailed(true));
  }, [token, router]);

  return failed ? (
    <>
      <h1 className="text-2xl font-bold">Link inválido ou expirado</h1>
      <Link href="/admin/login" className="underline">
        Pedir um novo link
      </Link>
    </>
  ) : (
    <p role="status">Validando seu acesso…</p>
  );
}
