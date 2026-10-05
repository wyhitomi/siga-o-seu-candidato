import Link from "next/link";
import { ParliamentarianCard } from "@/components/parliamentarian-card";
import { SearchForm } from "@/components/search-form";
import {
  KINDS,
  first,
  searchParliamentarians,
  type Kind,
  type SearchQuery,
} from "@/lib/parliamentarians";

type RawSearchParams = Record<string, string | string[] | undefined>;

function toQuery(raw: RawSearchParams): SearchQuery {
  const page = Number(first(raw.page) ?? "1");
  return {
    q: first(raw.q),
    uf: first(raw.uf)?.toUpperCase(),
    party: first(raw.party)?.toUpperCase(),
    page: Number.isInteger(page) && page > 0 ? page : 1,
  };
}

function pageHref(basePath: string, query: SearchQuery, page: number): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries({ ...query, page })) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  return `${basePath}?${params}`;
}

export async function ParliamentarianSearch({
  kind,
  searchParams,
}: {
  kind: Kind;
  searchParams: RawSearchParams;
}) {
  const config = KINDS[kind];
  const query = toQuery(searchParams);
  const result = await searchParliamentarians(kind, query);
  const hasFilters = Boolean(query.q || query.uf || query.party);

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold">{config.title}</h1>
        <p className="text-sm text-slate-600 dark:text-slate-400">{config.description}</p>
      </header>

      <SearchForm action={config.basePath} query={query} />

      {!result.ok ? (
        <p role="alert" className="rounded-lg bg-amber-50 p-4 text-amber-900">
          {result.error}
        </p>
      ) : result.data.total === 0 ? (
        <p className="text-slate-600 dark:text-slate-400">
          {hasFilters
            ? "Nenhum resultado para esses filtros."
            : "Os dados ainda não foram carregados. Volte em breve."}
        </p>
      ) : (
        <>
          <p className="text-sm text-slate-600 dark:text-slate-400" aria-live="polite">
            {result.data.total} resultado(s)
          </p>
          <ul className="grid gap-3 sm:grid-cols-2">
            {result.data.items.map((person) => (
              <ParliamentarianCard
                key={person.id}
                person={person}
                href={`${config.basePath}/${person.id}`}
              />
            ))}
          </ul>
          <Pagination
            basePath={config.basePath}
            query={query}
            page={result.data.page}
            lastPage={Math.ceil(result.data.total / result.data.page_size)}
          />
        </>
      )}
    </div>
  );
}

function Pagination({
  basePath,
  query,
  page,
  lastPage,
}: {
  basePath: string;
  query: SearchQuery;
  page: number;
  lastPage: number;
}) {
  if (lastPage <= 1) return null;
  return (
    <nav aria-label="Paginação" className="flex items-center justify-between text-sm">
      {page > 1 ? (
        <Link href={pageHref(basePath, query, page - 1)} className="hover:underline">
          ← Anterior
        </Link>
      ) : (
        <span />
      )}
      <span>
        Página {page} de {lastPage}
      </span>
      {page < lastPage ? (
        <Link href={pageHref(basePath, query, page + 1)} className="hover:underline">
          Próxima →
        </Link>
      ) : (
        <span />
      )}
    </nav>
  );
}
