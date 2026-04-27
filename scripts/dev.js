const { spawn } = require("node:child_process");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..");
const runtimeHost = process.env.EMBODIED_AGENT_HTTP_HOST || "127.0.0.1";
const runtimePort = process.env.EMBODIED_AGENT_HTTP_PORT || "7860";
const proxyTarget = process.env.VITE_PROXY_TARGET || `http://${runtimeHost}:${runtimePort}`;
const runtimeBaseUrl = process.env.VITE_RUNTIME_BASE_URL || `http://${runtimeHost}:${runtimePort}`;
const defaultPython = process.platform === "win32"
  ? path.join(repoRoot, ".venv", "Scripts", "python.exe")
  : path.join(repoRoot, ".venv", "bin", "python");
const pythonExe = process.env.EMBODIED_AGENT_PYTHON || defaultPython;
const pythonPath = [path.join(repoRoot, "src"), process.env.PYTHONPATH].filter(Boolean).join(path.delimiter);

const backend = spawn(
  pythonExe,
  ["-m", "embodied_agent.backend.http", "--host", runtimeHost, "--port", runtimePort],
  {
    stdio: "inherit",
    shell: true,
    env: {
      ...process.env,
      PYTHONPATH: pythonPath,
      EMBODIED_AGENT_HTTP_HOST: runtimeHost,
      EMBODIED_AGENT_HTTP_PORT: runtimePort,
    },
  },
);

const frontend = spawn("npm", ["--prefix", "frontend", "run", "dev"], {
  stdio: "inherit",
  shell: true,
  env: {
    ...process.env,
    EMBODIED_AGENT_HTTP_HOST: runtimeHost,
    EMBODIED_AGENT_HTTP_PORT: runtimePort,
    VITE_PROXY_TARGET: proxyTarget,
    VITE_RUNTIME_BASE_URL: runtimeBaseUrl,
  },
});

function shutdown(code = 0) {
  if (!backend.killed) {
    backend.kill();
  }
  if (!frontend.killed) {
    frontend.kill();
  }
  process.exit(code);
}

backend.on("exit", (code) => {
  if (code && code !== 0) {
    shutdown(code);
  }
});

frontend.on("exit", (code) => {
  if (code && code !== 0) {
    shutdown(code);
  }
});

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));
