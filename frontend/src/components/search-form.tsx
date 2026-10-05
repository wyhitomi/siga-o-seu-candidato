import { UFS, type SearchQuery } from "@/lib/parliamentarians";

export function SearchForm({ action, query }: { action: string; query: SearchQuery }) {
  return (
    <form action={action} method="get" role="search" className="grid gap-3 sm:grid-cols-[1fr_8rem_8rem_auto]">
      <label className="sr-only" htmlFor="q">
        Nome
      </label>
      <input
        id="q"
        name="q"
        type="search"
        minLength={2}
        defaultValue={query.q}
        placeholder="Nome (ex.: Maria, jose silva)"
        className="rounded-lg border border-slate-300 bg-transparent px-3 py-2 dark:border-slate-700"
      />
      <label className="sr-only" htmlFor="uf">
        Estado
      </label>
      <select
        id="uf"
        name="uf"
        defaultValue={query.uf ?? ""}
        className="rounded-lg border border-slate-300 bg-transparent px-3 py-2 dark:border-slate-700"
      >
        <option value="">Todos os estados</option>
        {UFS.map((uf) => (
          <option key={uf} value={uf}>
            {uf}
          </option>
        ))}
      </select>
      <label className="sr-only" htmlFor="party">
        Partido
      </label>
      <input
        id="party"
        name="party"
        defaultValue={query.party}
        placeholder="Partido"
        className="rounded-lg border border-slate-300 bg-transparent px-3 py-2 uppercase dark:border-slate-700"
      />
      <button
        type="submit"
        className="rounded-lg bg-emerald-700 px-5 py-2 font-medium text-white hover:bg-emerald-800"
      >
        Buscar
      </button>
    </form>
  );
}
