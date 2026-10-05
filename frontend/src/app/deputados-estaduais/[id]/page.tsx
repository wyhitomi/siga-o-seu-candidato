import { ParliamentarianDetail } from "@/components/parliamentarian-detail";

export default async function StateDeputyPage(props: PageProps<"/deputados-estaduais/[id]">) {
  const { id } = await props.params;
  return <ParliamentarianDetail kind="state-deputies" id={id} />;
}
