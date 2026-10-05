import { ParliamentarianDetail } from "@/components/parliamentarian-detail";

export default async function SenatorPage(props: PageProps<"/senadores/[id]">) {
  const { id } = await props.params;
  return <ParliamentarianDetail kind="senators" id={id} />;
}
