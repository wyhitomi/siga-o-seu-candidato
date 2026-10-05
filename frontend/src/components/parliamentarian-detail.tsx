import Link from "next/link";
import { notFound } from "next/navigation";
import { Avatar } from "@/components/parliamentarian-card";
import { KINDS, formatDate, getParliamentarian, type Kind } from "@/lib/parliamentarians";

export async function ParliamentarianDetail({ kind, id }: { kind: Kind; id: string }) {
  const numericId = Number(id);
  if (!Number.isInteger(numericId) || numericId <= 0) notFound();
  const person = await getParliamentarian(kind, numericId);
  if (!person) notFound();

  const config = KINDS[kind];
  const mandate = [formatDate(person.mandate_start), formatDate(person.mandate_end)]
    .filter(Boolean)
    .join(" a ");
  const facts: [string, string | null | undefined][] = [
    ["Nome completo", person.full_name],
    ["Cargo", person.role],
    ["Partido", person.party],
    ["Estado", person.uf],
    ["Situação", person.status],
    ["Mandato", mandate || null],
    ["E-mail institucional", person.email],
  ];

  return (
    <article className="space-y-6">
      <Link href={config.basePath} className="text-sm hover:underline">
        ← Voltar para {config.title.toLowerCase()}
      </Link>
      <header className="flex items-center gap-5">
        <Avatar person={person} size={96} />
        <div>
          <h1 className="text-2xl font-bold">{person.name}</h1>
          <p className="text-slate-600 dark:text-slate-400">
            {[person.role, person.party, person.uf].filter(Boolean).join(" · ")}
          </p>
        </div>
      </header>
      <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-[12rem_1fr]">
        {facts
          .filter(([, value]) => value)
          .map(([label, value]) => (
            <div key={label} className="contents">
              <dt className="text-sm text-slate-500">{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
      </dl>
      <footer className="text-xs text-slate-500">
        Fonte: {person.source === "senado" ? "Senado Federal" : "TSE"} · dados coletados em{" "}
        {new Date(person.fetched_at).toLocaleString("pt-BR")}
        {person.profile_url ? (
          <>
            {" · "}
            <a href={person.profile_url} className="underline" target="_blank" rel="noreferrer">
              página oficial
            </a>
          </>
        ) : null}
      </footer>
    </article>
  );
}
