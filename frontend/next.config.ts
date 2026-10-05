import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    // Official photos served by the Senate
    remotePatterns: [{ protocol: "https", hostname: "www.senado.leg.br" }],
  },
};

export default nextConfig;
