import type { Metadata } from "next";
import { ParliamentarianSearch } from "@/components/parliamentarian-search";

export const metadata: Metadata = { title: "Senadores" };

export default async function SenatorsPage(props: PageProps<"/senadores">) {
  return <ParliamentarianSearch kind="senators" searchParams={await props.searchParams} />;
}
