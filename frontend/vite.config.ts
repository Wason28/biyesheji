import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const runtimeHost = env.EMBODIED_AGENT_HTTP_HOST || "127.0.0.1";
  const runtimePort = env.EMBODIED_AGENT_HTTP_PORT || "7860";
  const proxyTarget = env.VITE_PROXY_TARGET || `http://${runtimeHost}:${runtimePort}`;

  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
