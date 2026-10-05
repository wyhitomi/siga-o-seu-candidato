import { api, type Parliamentarian, type ParliamentarianPage } from "./api/client";

export type Kind = "senators" | "state-deputies";

export const KINDS = {
  senators: {
    basePath: "/senadores",
    title: "Senadores",
    singular: "senador(a)",
    description: "Senadores em exercício. Fonte: Dados Abertos do Senado Federal.",
  },
  "state-deputies": {
    basePath: "/deputados-estaduais",
    title: "Deputados estaduais",
    singular: "deputado(a) estadual",
    description:
      "Deputados estaduais e distritais eleitos em 2022. Fonte: TSE Dados Abertos.",
  },
} as const satisfies Record<Kind, object>;

export type SearchQuery = {
  q?: string;
  uf?: string;
  party?: string;
  page?: number;
};

type Result<T> = { ok: true; data: T } | { ok: false; error: string };

const UNAVAILABLE = "A fonte de dados está indisponível no momento. Tente novamente em instantes.";

function errorMessage(status: number): string {
  if (status === 503) return UNAVAILABLE;
  if (status === 422) return "Confira os filtros da busca.";
  return "Não foi possível concluir a busca.";
}

export async function searchParliamentarians(
  kind: Kind,
  query: SearchQuery,
): Promise<Result<ParliamentarianPage>> {
  try {
    const { data, response } =
      kind === "senators"
        ? await api.GET("/api/v1/senators", { params: { query } })
        : await api.GET("/api/v1/state-deputies", { params: { query } });
    return data ? { ok: true, data } : { ok: false, error: errorMessage(response.status) };
  } catch {
    return { ok: false, error: UNAVAILABLE };
  }
}

export async function getParliamentarian(
  kind: Kind,
  id: number,
): Promise<Parliamentarian | null> {
  const { data } =
    kind === "senators"
      ? await api.GET("/api/v1/senators/{senator_id}", { params: { path: { senator_id: id } } })
      : await api.GET("/api/v1/state-deputies/{deputy_id}", {
          params: { path: { deputy_id: id } },
        });
  return data ?? null;
}

export const UFS = [
  "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
  "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
] as const;

export function first(value: string | string[] | undefined): string | undefined {
  const v = Array.isArray(value) ? value[0] : value;
  return v?.trim() || undefined;
}

export function formatDate(value: string | null | undefined): string | null {
  if (!value) return null;
  return new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString("pt-BR");
}
