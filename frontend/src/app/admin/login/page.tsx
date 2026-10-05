"use client";

import { useState, type FormEvent } from "react";
import { api } from "@/lib/api/client";

type State = "idle" | "sending" | "sent" | "error";

export default function AdminLoginPage() {
  const [state, setState] = useState<State>("idle");
  const [message, setMessage] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = String(new FormData(event.currentTarget).get("email") ?? "");
    setState("sending");
    try {
      const { data, response } = await api.POST("/api/v1/auth/magic-link", { body: { email } });
      if (data) {
        setState("sent");
        setMessage(data.detail ?? "Verifique seu e-mail.");
      } else {
        setState("error");
        setMessage(
          response.status === 429
            ? "Muitas tentativas. Aguarde alguns minutos."
            : "Confira o e-mail informado.",
        );
      }
    } catch {
      setState("error");
      setMessage("Não foi possível falar com o servidor.");
    }
  }

  return (
    <>
      <h1 className="text-2xl font-bold">Entrar como administrador</h1>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Área restrita. Enviaremos um link de acesso, válido por alguns minutos, para o e-mail de
        administradores cadastrados.
      </p>
      <form onSubmit={onSubmit} className="space-y-3">
        <label htmlFor="email" className="block text-sm font-medium">
          E-mail
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 dark:border-slate-700"
        />
        <button
          type="submit"
          disabled={state === "sending"}
          className="w-full rounded-lg bg-emerald-700 px-5 py-2 font-medium text-white hover:bg-emerald-800 disabled:opacity-60"
        >
          {state === "sending" ? "Enviando…" : "Enviar link de acesso"}
        </button>
      </form>
      {message ? (
        <p role="status" className={state === "error" ? "text-red-700" : "text-emerald-800"}>
          {message}
        </p>
      ) : null}
    </>
  );
}
