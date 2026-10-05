import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

// Server components can reach the API on an internal URL (e.g. inside Docker);
// the browser always uses the public one.
const baseUrl =
  typeof window === "undefined"
    ? (process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

export const api = createClient<paths>({ baseUrl, cache: "no-store" });

export type Parliamentarian = components["schemas"]["ParliamentarianOut"];
export type ParliamentarianPage = components["schemas"]["ParliamentarianPage"];
