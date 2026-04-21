import { create } from "zustand";

import {
  getBootstrap,
  getConfig,
  getRunState,
  getTools,
  RuntimeRequestError,
  runtimeBaseUrl,
  startRun,
} from "../lib/api";
import { createRuntimeEventSource } from "../lib/sse";
import type {
  ConfigSectionKey,
  FrontendBootstrapPayload,
  FrontendRunAcceptedPayload,
  FrontendRunSnapshot,
  FrontendRunStatePayload,
  FrontendToolDescriptor,
} from "../types/runtime";

type AsyncStatus = "idle" | "loading" | "ready" | "error";
type StreamStatus = "idle" | "connecting" | "live" | "closed" | "error";

interface WorkbenchState {
  runtimeBaseUrl: string;
  instruction: string;
  requestedRunId: string;
  bootstrapStatus: AsyncStatus;
  configStatus: AsyncStatus;
  toolsStatus: AsyncStatus;
  runStatus: AsyncStatus;
  streamStatus: StreamStatus;
  latestError: string;
  latestErrorCode: string;
  streamNotice: string;
  activeConfigTab: ConfigSectionKey;
  bootstrap: FrontendBootstrapPayload | null;
  config: FrontendBootstrapPayload["config"] | null;
  tools: FrontendToolDescriptor[];
  snapshot: FrontendRunSnapshot | null;
  runAccepted: FrontendRunAcceptedPayload | null;
  latestRunState: FrontendRunStatePayload | null;
  eventFeed: FrontendRunStatePayload[];
  eventSource: EventSource | null;
  initialize: () => Promise<void>;
  refreshConfig: () => Promise<void>;
  refreshTools: () => Promise<void>;
  submitRun: () => Promise<void>;
  syncRunSnapshot: () => Promise<void>;
  setInstruction: (value: string) => void;
  setRequestedRunId: (value: string) => void;
  clearInstruction: () => void;
  setActiveConfigTab: (tab: ConfigSectionKey) => void;
  disconnectStream: () => void;
}

function dedupeEvents(events: FrontendRunStatePayload[]) {
  const latestByVersion = new Map<number, FrontendRunStatePayload>();
  events.forEach((event) => {
    latestByVersion.set(event.version, event);
  });
  return [...latestByVersion.values()].sort((left, right) => left.version - right.version);
}

function closeEventSource(source: EventSource | null) {
  if (source) {
    source.close();
  }
}

function upsertRunEvent(
  currentEvents: FrontendRunStatePayload[],
  nextEvent: FrontendRunStatePayload,
) {
  return dedupeEvents([...currentEvents, nextEvent]);
}

export const useWorkbenchStore = create<WorkbenchState>((set, get) => ({
  runtimeBaseUrl,
  instruction: "",
  requestedRunId: "",
  bootstrapStatus: "idle",
  configStatus: "idle",
  toolsStatus: "idle",
  runStatus: "idle",
  streamStatus: "idle",
  latestError: "",
  latestErrorCode: "",
  streamNotice: "等待启动 run 以建立事件订阅。",
  activeConfigTab: "decision",
  bootstrap: null,
  config: null,
  tools: [],
  snapshot: null,
  runAccepted: null,
  latestRunState: null,
  eventFeed: [],
  eventSource: null,
  async initialize() {
    set({
      bootstrapStatus: "loading",
      configStatus: "loading",
      toolsStatus: "loading",
      latestError: "",
      latestErrorCode: "",
    });
    try {
      const [bootstrap, config, toolsPayload] = await Promise.all([
        getBootstrap(),
        getConfig(),
        getTools(),
      ]);
      set({
        bootstrap,
        config,
        tools: toolsPayload.tools,
        bootstrapStatus: "ready",
        configStatus: "ready",
        toolsStatus: "ready",
        latestError: "",
        latestErrorCode: "",
      });
    } catch (error) {
      const message =
        error instanceof RuntimeRequestError ? error.message : "加载 bootstrap 失败";
      set({
        bootstrapStatus: "error",
        configStatus: "error",
        toolsStatus: "error",
        latestError: message,
        latestErrorCode: error instanceof RuntimeRequestError ? error.code : "BootstrapLoadFailed",
      });
    }
  },
  async refreshConfig() {
    set({
      configStatus: "loading",
      latestError: "",
      latestErrorCode: "",
    });
    try {
      const config = await getConfig();
      set({
        config,
        configStatus: "ready",
      });
    } catch (error) {
      const message =
        error instanceof RuntimeRequestError ? error.message : "刷新配置失败";
      set({
        configStatus: "error",
        latestError: message,
        latestErrorCode: error instanceof RuntimeRequestError ? error.code : "ConfigRefreshFailed",
      });
    }
  },
  async refreshTools() {
    set({
      toolsStatus: "loading",
      latestError: "",
      latestErrorCode: "",
    });
    try {
      const payload = await getTools();
      set({
        tools: payload.tools,
        toolsStatus: "ready",
      });
    } catch (error) {
      const message =
        error instanceof RuntimeRequestError ? error.message : "刷新工具列表失败";
      set({
        toolsStatus: "error",
        latestError: message,
        latestErrorCode: error instanceof RuntimeRequestError ? error.code : "ToolsRefreshFailed",
      });
    }
  },
  async submitRun() {
    const instruction = get().instruction.trim();
    const requestedRunId = get().requestedRunId.trim();
    if (!instruction) {
      set({
        latestError: "请输入任务指令后再启动。",
        latestErrorCode: "InvalidInstruction",
      });
      return;
    }

    closeEventSource(get().eventSource);
    set({
      runStatus: "loading",
      streamStatus: "connecting",
      latestError: "",
      latestErrorCode: "",
      streamNotice: "正在创建 run 并订阅 snapshot 事件。",
      runAccepted: null,
      latestRunState: null,
      eventFeed: [],
      eventSource: null,
    });

    try {
      const accepted = await startRun(instruction, requestedRunId || undefined);
      set({
        runAccepted: accepted,
        snapshot: accepted.run,
        runStatus: "ready",
        latestErrorCode: "",
        streamNotice: "run 已接受，正在连接事件流。",
      });
      await get().syncRunSnapshot();

      const source = createRuntimeEventSource(accepted.events_url);

      source.onopen = () => {
        set({
          streamStatus: "live",
          streamNotice: "已连接 snapshot 事件流。",
        });
      };

      source.addEventListener("snapshot", (event) => {
        const payload = JSON.parse((event as MessageEvent<string>).data) as FrontendRunStatePayload;
        set((state) => ({
          snapshot: payload.run,
          latestRunState: payload,
          eventFeed: upsertRunEvent(state.eventFeed, payload),
          streamStatus: payload.terminal ? "closed" : "live",
          streamNotice: payload.terminal
            ? "收到终态 snapshot，事件订阅已收口。"
            : `已收到版本 ${payload.version} 的 snapshot 事件。`,
        }));
        if (payload.terminal) {
          source.close();
          set({
            eventSource: null,
          });
        }
      });

      source.onerror = () => {
        void get().syncRunSnapshot();
        set({
          streamStatus:
            source.readyState === EventSource.CONNECTING ? "connecting" : "error",
          streamNotice:
            source.readyState === EventSource.CONNECTING
              ? "后端 SSE 为回放式骨架，浏览器正在尝试续连。"
              : "事件流暂时不可用。",
        });
      };

      set({
        eventSource: source,
      });
    } catch (error) {
      const message =
        error instanceof RuntimeRequestError ? error.message : "启动 run 失败";
      set({
        runStatus: "error",
        streamStatus: "error",
        latestError: message,
        latestErrorCode: error instanceof RuntimeRequestError ? error.code : "RunStartFailed",
        streamNotice: "run 创建失败，未建立事件订阅。",
      });
    }
  },
  async syncRunSnapshot() {
    const accepted = get().runAccepted;
    if (!accepted?.snapshot_url) {
      return;
    }
    try {
      const payload = await getRunState(accepted.snapshot_url);
      set((state) => ({
        snapshot: payload.run,
        latestRunState: payload,
        eventFeed: upsertRunEvent(state.eventFeed, payload),
        streamNotice: payload.terminal
          ? "已通过 snapshot_url 同步到终态快照。"
          : `已通过 snapshot_url 同步到版本 ${payload.version}。`,
      }));
    } catch (error) {
      const message =
        error instanceof RuntimeRequestError ? error.message : "同步 run 快照失败";
      set({
        latestError: message,
        latestErrorCode: error instanceof RuntimeRequestError ? error.code : "RunSnapshotSyncFailed",
      });
    }
  },
  setInstruction(value) {
    set({
      instruction: value,
    });
  },
  setRequestedRunId(value) {
    set({
      requestedRunId: value,
    });
  },
  clearInstruction() {
    set({
      instruction: "",
      requestedRunId: "",
    });
  },
  setActiveConfigTab(tab) {
    set({
      activeConfigTab: tab,
    });
  },
  disconnectStream() {
    closeEventSource(get().eventSource);
    set({
      eventSource: null,
      streamStatus: "closed",
      streamNotice: "事件订阅已手动断开。",
    });
  },
}));
