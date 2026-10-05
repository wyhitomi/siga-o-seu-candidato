import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Administração",
  robots: { index: false, follow: false },
};

export default function AdminLayout({ children }: LayoutProps<"/admin">) {
  return <div className="mx-auto max-w-md space-y-6">{children}</div>;
}
