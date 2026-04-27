import type {
  FrontendBootstrapPayload,
  FrontendConfigPayload,
  FrontendErrorPayload,
  FrontendRunAcceptedPayload,
  FrontendRunStatePayload,
  FrontendToolsPayload,
} from "../types/runtime";

const RAW_BASE_URL = (import.meta.env.VITE_RUNTIME_BASE_URL || "").trim();

export const runtimeBaseUrl = RAW_BASE_URL.replace(/\/$/, "");

export class RuntimeRequestError extends Error {
  code: string;
  status: number;

  constructor(
    message: string,
    options: {
      code?: string;
      status?: number;
    } = {},
  ) {
    super(message);
    this.name = "RuntimeRequestError";
    this.code = options.code || "UnknownError";
    this.status = options.status || 500;
  }
}

export function resolveRuntimeUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  if (!path.startsWith("/")) {
    return `${runtimeBaseUrl}/${path}`;
  }
  return `${runtimeBaseUrl}${path}`;
}

async function requestJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(resolveRuntimeUrl(path), {
    headers: {
      Accept: "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const errorPayload = payload as FrontendErrorPayload | null;
    throw new RuntimeRequestError(
      errorPayload?.error?.message || `请求失败: ${response.status}`,
      {
        code: errorPayload?.error?.code || "HttpError",
        status: response.status,
      },
    );
  }

  return payload as T;
}

export function getBootstrap() {
  return requestJSON<FrontendBootstrapPayload>("/api/v1/runtime/bootstrap");
}

export function getConfig() {
  return requestJSON<FrontendConfigPayload>("/api/v1/runtime/config");
}

export function updateConfig(config: FrontendConfigPayload) {
  return requestJSON<FrontendConfigPayload>("/api/v1/runtime/config", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(config),
  });
}

export function getTools() {
  return requestJSON<FrontendToolsPayload>("/api/v1/runtime/tools");
}

export function refreshTools() {
  return requestJSON<FrontendToolsPayload>("/api/v1/runtime/tools/refresh", {
    method: "POST",
  });
}

export function getRunState(path: string) {
  return requestJSON<FrontendRunStatePayload>(path);
}

export function startRun(instruction: string, runId?: string) {
  return requestJSON<FrontendRunAcceptedPayload>("/api/v1/runtime/runs", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      instruction,
      ...(runId ? { run_id: runId } : {}),
    }),
  });
}

export function stopRun(snapshotUrl: string) {
  const stopPath = snapshotUrl.replace(/\/$/, "").concat("/stop");
  return requestJSON<FrontendRunStatePayload>(stopPath, {
    method: "POST",
  });
}
