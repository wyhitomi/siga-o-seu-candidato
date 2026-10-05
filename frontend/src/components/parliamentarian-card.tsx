import Image from "next/image";
import Link from "next/link";
import type { Parliamentarian } from "@/lib/api/client";

export function Avatar({ person, size }: { person: Parliamentarian; size: number }) {
  if (person.photo_url) {
    return (
      <Image
        src={person.photo_url}
        alt={`Foto de ${person.name}`}
        width={size}
        height={size}
        className="rounded-full object-cover"
        style={{ width: size, height: size }}
      />
    );
  }
  const initials = person.name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("");
  return (
    <div
      aria-hidden
      className="flex items-center justify-center rounded-full bg-emerald-100 font-semibold text-emerald-800"
      style={{ width: size, height: size }}
    >
      {initials}
    </div>
  );
}

export function ParliamentarianCard({ person, href }: { person: Parliamentarian; href: string }) {
  return (
    <li>
      <Link
        href={href}
        className="flex items-center gap-4 rounded-xl border border-slate-200 p-4 transition hover:border-emerald-600 dark:border-slate-800"
      >
        <Avatar person={person} size={56} />
        <div className="min-w-0">
          <p className="truncate font-medium">{person.name}</p>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {[person.party, person.uf].filter(Boolean).join(" · ")}
          </p>
        </div>
      </Link>
    </li>
  );
}
