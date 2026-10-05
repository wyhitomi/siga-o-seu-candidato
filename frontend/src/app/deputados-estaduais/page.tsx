import type { Metadata } from "next";
import { ParliamentarianSearch } from "@/components/parliamentarian-search";

export const metadata: Metadata = { title: "Deputados estaduais" };

export default async function StateDeputiesPage(props: PageProps<"/deputados-estaduais">) {
  return <ParliamentarianSearch kind="state-deputies" searchParams={await props.searchParams} />;
}
