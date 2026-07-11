import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Lean, self-contained server output for the production Docker image
  // (web/Dockerfile) — copies only what's needed to run, not the full
  // node_modules tree.
  output: "standalone",
};

export default nextConfig;
