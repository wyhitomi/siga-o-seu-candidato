"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { authHeader, clearToken, getToken } from "@/lib/admin-session";
import { api } from "@/lib/api/client";
import { UFS } from "@/lib/parliamentarians";

export default function AdminPage() {
  const router = useRouter();
  const [token, setTokenState] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [uf, setUf] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const stored = getToken();
    if (!stored) {
      router.replace("/admin/login");
      return;
    }
    api.GET("/api/v1/auth/me", { headers: authHeader(stored) }).then(({ data }) => {
      if (!data) {
        clearToken();
        router.replace("/admin/login");
        return;
      }
      setTokenState(stored);
      setEmail(data.email);
    });
  }, [router]);

  async function run(action: () => Promise<string>) {
    setBusy(true);
    setMessage("");
    try {
      setMessage(await action());
    } catch {
      setMessage("Não foi possível falar com o servidor.");
    } finally {
      setBusy(false);
    }
  }

  function syncSenators() {
    return run(async () => {
      const { data, response } = await api.POST("/api/v1/admin/sync/senators", {
        headers: authHeader(token!),
      });
      return data
        ? `${data.stored} senadores atualizados.`
        : `Falha ao atualizar senadores (HTTP ${response.status}).`;
    });
  }

  function syncStateDeputies() {
    return run(async () => {
      const { data, response } = await api.POST("/api/v1/admin/sync/state-deputies", {
        headers: authHeader(token!),
        params: { query: uf ? { uf } : {} },
      });
      return data
        ? `Carga de deputados ${uf ? `de ${uf} ` : ""}agendada. Pode levar alguns minutos.`
        : `Falha ao agendar carga (HTTP ${response.status}).`;
    });
  }

  function logout() {
    clearToken();
    router.replace("/admin/login");
  }

  if (!email) return <p role="status">Carregando…</p>;

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Administração</h1>
        <button onClick={logout} className="text-sm underline">
          Sair
        </button>
      </div>
      <p className="text-sm text-slate-600 dark:text-slate-400">Conectado como {email}</p>

      <section className="space-y-3 rounded-xl border border-slate-200 p-4 dark:border-slate-800">
        <h2 className="font-semibold">Senadores</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Busca a lista atual no Senado Federal.
        </p>
        <button
          onClick={syncSenators}
          disabled={busy}
          className="rounded-lg bg-emerald-700 px-4 py-2 text-white disabled:opacity-60"
        >
          Atualizar agora
        </button>
      </section>

      <section className="space-y-3 rounded-xl border border-slate-200 p-4 dark:border-slate-800">
        <h2 className="font-semibold">Deputados estaduais</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Carrega os eleitos a partir dos dados abertos do TSE (arquivo grande, roda em segundo
          plano).
        </p>
        <div className="flex gap-3">
          <select
            value={uf}
            onChange={(e) => setUf(e.target.value)}
            aria-label="Estado"
            className="rounded-lg border border-slate-300 bg-transparent px-3 py-2 dark:border-slate-700"
          >
            <option value="">Todos os estados</option>
            {UFS.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
          <button
            onClick={syncStateDeputies}
            disabled={busy}
            className="rounded-lg bg-emerald-700 px-4 py-2 text-white disabled:opacity-60"
          >
            Carregar
          </button>
        </div>
      </section>

      {message ? <p role="status">{message}</p> : null}
    </>
  );
}
