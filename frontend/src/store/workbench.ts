import { create } from "zustand";

import {
  getBootstrap,
  getConfig,
  getRunState,
  getTools,
  refreshTools as requestToolsRefresh,
  RuntimeRequestError,
  runtimeBaseUrl,
  startRun,
  updateConfig,
} from "../lib/api";
import { createRuntimeEventSource } from "../lib/sse";
import type {
  ConfigSectionKey,
  FrontendBootstrapPayload,
  FrontendConfigPayload,
  FrontendRunAcceptedPayload,
  FrontendRunSnapshot,
  FrontendRunStatePayload,
  FrontendToolDescriptor,
} from "../types/runtime";

type AsyncStatus = "idle" | "loading" | "ready" | "error";
type StreamStatus = "idle" | "connecting" | "live" | "closed" | "error";
type ThemeMode = "dark" | "light";

interface WorkbenchState {
  runtimeBaseUrl: string;
  themeMode: ThemeMode;
  showRuntimeDetails: boolean;
  showToolSchemas: boolean;
  showModelAssistants: boolean;
  instruction: string;
  requestedRunId: string;
  bootstrapStatus: AsyncStatus;
  configStatus: AsyncStatus;
  toolsStatus: AsyncStatus;
  runStatus: AsyncStatus;
  streamStatus: StreamStatus;
  configDraftStatus: AsyncStatus;
  latestError: string;
  latestErrorCode: string;
  streamNotice: string;
  toolsNotice: string;
  configNotice: string;
  lastRunSummary: string;
  activeConfigTab: ConfigSectionKey;
  bootstrap: FrontendBootstrapPayload | null;
  config: FrontendConfigPayload | null;
  configDraft: FrontendConfigPayload | null;
  tools: FrontendToolDescriptor[];
  snapshot: FrontendRunSnapshot | null;
  runAccepted: FrontendRunAcceptedPayload | null;
  latestRunState: FrontendRunStatePayload | null;
  eventFeed: FrontendRunStatePayload[];
  eventSource: EventSource | null;
  initialize: () => Promise<void>;
  refreshConfig: () => Promise<void>;
  refreshTools: () => Promise<void>;
  saveConfigDraft: () => Promise<void>;
  resetConfigDraft: () => void;
  submitRun: () => Promise<void>;
  syncRunSnapshot: () => Promise<void>;
  setInstruction: (value: string) => void;
  setRequestedRunId: (value: string) => void;
  updateConfigDraft: (
    section: ConfigSectionKey,
    field: string,
    value: string | number,
  ) => void;
  updateHomePoseDraft: (axis: string, value: number) => void;
  setThemeMode: (mode: ThemeMode) => void;
  toggleRuntimeDetails: () => void;
  toggleToolSchemas: () => void;
  toggleModelAssistants: () => void;
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

function cloneConfig(config: FrontendConfigPayload | null) {
  return config ? JSON.parse(JSON.stringify(config)) as FrontendConfigPayload : null;
}

export const useWorkbenchStore = create<WorkbenchState>((set, get) => ({
  runtimeBaseUrl,
  themeMode: "dark",
  showRuntimeDetails: false,
  showToolSchemas: false,
  showModelAssistants: false,
  instruction: "",
  requestedRunId: "",
  bootstrapStatus: "idle",
  configStatus: "idle",
  toolsStatus: "idle",
  runStatus: "idle",
  streamStatus: "idle",
  configDraftStatus: "idle",
  latestError: "",
  latestErrorCode: "",
  streamNotice: "等待启动 run 以建立事件订阅。",
  toolsNotice: "当前工具列表来自 bootstrap / tools 合同。",
  configNotice: "当前配置支持展示、编辑、提交与回滚。",
  lastRunSummary: "尚未执行本地闭环 run。",
  activeConfigTab: "decision",
  bootstrap: null,
  config: null,
  configDraft: null,
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
        configDraft: cloneConfig(config),
        tools: toolsPayload.tools,
        bootstrapStatus: "ready",
        configStatus: "ready",
        toolsStatus: "ready",
        latestError: "",
        latestErrorCode: "",
        toolsNotice: `已加载 ${toolsPayload.tools.length} 个工具描述。`,
        configNotice: "配置已加载，可按分区编辑后提交。",
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
        configDraft: cloneConfig(config),
        configStatus: "ready",
        configNotice: "已从后端刷新配置，并重置当前草稿。",
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
      const payload = await requestToolsRefresh();
      set({
        tools: payload.tools,
        toolsStatus: "ready",
        toolsNotice: `工具列表已刷新，当前共 ${payload.tools.length} 项。`,
      });
    } catch (error) {
      const message =
        error instanceof RuntimeRequestError ? error.message : "刷新工具列表失败";
      set({
        toolsStatus: "error",
        latestError: message,
        latestErrorCode: error instanceof RuntimeRequestError ? error.code : "ToolsRefreshFailed",
        toolsNotice: "工具刷新失败，当前保留最近一次成功结果。",
      });
    }
  },
  async saveConfigDraft() {
    const configDraft = get().configDraft;
    if (!configDraft) {
      return;
    }
    set({
      configDraftStatus: "loading",
      latestError: "",
      latestErrorCode: "",
    });
    try {
      const config = await updateConfig(configDraft);
      set({
        config,
        configDraft: cloneConfig(config),
        configStatus: "ready",
        configDraftStatus: "ready",
        configNotice: "配置已提交并与后端完成同步。",
      });
    } catch (error) {
      const message =
        error instanceof RuntimeRequestError ? error.message : "提交配置失败";
      set({
        configDraftStatus: "error",
        latestError: message,
        latestErrorCode: error instanceof RuntimeRequestError ? error.code : "ConfigUpdateFailed",
      });
    }
  },
  resetConfigDraft() {
    set((state) => ({
      configDraft: cloneConfig(state.config),
      configDraftStatus: "idle",
      configNotice: "配置草稿已回滚到最近一次后端快照。",
    }));
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
          lastRunSummary: payload.terminal
            ? `最近一次 run 终态：${payload.run.status}（版本 ${payload.version}）。`
            : state.lastRunSummary,
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
        lastRunSummary: payload.terminal
          ? `最近一次 run 终态：${payload.run.status}（版本 ${payload.version}）。`
          : state.lastRunSummary,
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
  updateConfigDraft(section, field, value) {
    set((state) => {
      if (!state.configDraft) {
        return {};
      }
      return {
        configDraft: {
          ...state.configDraft,
          [section]: {
            ...state.configDraft[section],
            [field]: value,
          },
        },
        configDraftStatus: "idle",
      };
    });
  },
  updateHomePoseDraft(axis, value) {
    set((state) => {
      if (!state.configDraft) {
        return {};
      }
      return {
        configDraft: {
          ...state.configDraft,
          execution: {
            ...state.configDraft.execution,
            home_pose: {
              ...state.configDraft.execution.home_pose,
              [axis]: value,
            },
          },
        },
        configDraftStatus: "idle",
      };
    });
  },
  setThemeMode(mode) {
    set({
      themeMode: mode,
    });
  },
  toggleRuntimeDetails() {
    set((state) => ({
      showRuntimeDetails: !state.showRuntimeDetails,
    }));
  },
  toggleToolSchemas() {
    set((state) => ({
      showToolSchemas: !state.showToolSchemas,
    }));
  },
  toggleModelAssistants() {
    set((state) => ({
      showModelAssistants: !state.showModelAssistants,
    }));
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
