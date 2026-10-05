import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Siga o seu candidato",
    template: "%s · Siga o seu candidato",
  },
  description:
    "Acompanhe o que seus representantes eleitos fazem, com dados públicos e sem cadastro.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <header className="border-b border-slate-200 dark:border-slate-800">
          <nav className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-4">
            <Link href="/" className="font-semibold">
              Siga o seu candidato
            </Link>
            <Link href="/senadores" className="text-sm hover:underline">
              Senadores
            </Link>
            <Link href="/deputados-estaduais" className="text-sm hover:underline">
              Deputados estaduais
            </Link>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-slate-200 px-4 py-6 text-center text-xs text-slate-500 dark:border-slate-800">
          Dados públicos do Senado Federal e do TSE. Sem cadastro, sem cookies de rastreamento.
        </footer>
      </body>
    </html>
  );
}
