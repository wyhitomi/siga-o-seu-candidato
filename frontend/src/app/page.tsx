import Link from "next/link";

const SECTIONS = [
  {
    href: "/senadores",
    title: "Senadores",
    description: "Os 81 senadores em exercício, por nome, estado ou partido.",
  },
  {
    href: "/deputados-estaduais",
    title: "Deputados estaduais",
    description: "Deputados estaduais e distritais eleitos em todo o Brasil.",
  },
] as const;

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight">Quem governa por você?</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">
          Pesquise seus representantes eleitos com dados oficiais e públicos. Não é preciso
          criar conta e nada do que você pesquisa fica associado a você.
        </p>
      </section>
      <section className="grid gap-4 sm:grid-cols-2">
        {SECTIONS.map((s) => (
          <Link
            key={s.href}
            href={s.href}
            className="rounded-xl border border-slate-200 p-6 transition hover:border-emerald-600 hover:shadow-sm dark:border-slate-800"
          >
            <h2 className="text-lg font-semibold">{s.title}</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{s.description}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
