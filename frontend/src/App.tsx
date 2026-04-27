import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  Play,
  Square,
  Mic,
  Send,
  Settings,
  Sun,
  Moon,
  Video,
  Cpu,
  Activity,
  ChevronRight,
  Layers,
  CheckCircle2,
} from "lucide-react";

import { resolveRuntimeUrl } from "./lib/api";
import type { FrontendRunStatePayload, RunPhase } from "./types/runtime";
import { SettingsModal } from "./components/settings-modal";
import { useWorkbenchStore } from "./store/workbench";

type FlowNodeId =
  | "trigger"
  | "nlu"
  | "sensory"
  | "assessment"
  | "active_perception"
  | "task_planning"
  | "pre_feedback"
  | "motion_control"
  | "verification"
  | "error_diagnosis"
  | "hri"
  | "compensation"
  | "success_notice"
  | "goal_check"
  | "state_compression"
  | "final_status";

type FlowNodeStatus = "idle" | "active" | "completed" | "failed" | "attention";

const FLOW_SECTIONS: Array<{
  title: string;
  nodes: Array<{ id: FlowNodeId; label: string; variant?: "default" | "check" }>;
}> = [
  {
    title: "环境感知与理解层",
    nodes: [
      { id: "trigger", label: "交互触发与指令采集" },
      { id: "nlu", label: "语义解析与目标提取" },
      { id: "sensory", label: "多模态环境感知" },
      { id: "assessment", label: "状态置信度评估" },
      { id: "active_perception", label: "主动感知策略调整" },
    ],
  },
  {
    title: "决策规划层",
    nodes: [{ id: "task_planning", label: "任务分解与路径规划" }],
  },
  {
    title: "动作执行与反馈层",
    nodes: [
      { id: "pre_feedback", label: "执行前状态反馈" },
      { id: "motion_control", label: "动力学执行控制" },
      { id: "verification", label: "执行结果验证", variant: "check" },
    ],
  },
  {
    title: "异常处理与恢复机制",
    nodes: [
      { id: "error_diagnosis", label: "错误诊断" },
      { id: "hri", label: "人工干预/协同策略" },
      { id: "compensation", label: "补偿控制与重试" },
    ],
  },
  {
    title: "记忆与状态更新",
    nodes: [
      { id: "success_notice", label: "完成信号反馈" },
      { id: "goal_check", label: "任务终态判断", variant: "check" },
      { id: "state_compression", label: "环境状态压缩与记忆更新" },
      { id: "final_status", label: "输出执行报告", variant: "check" },
    ],
  },
];

interface NodeProps {
  id: FlowNodeId;
  label: string;
  status: FlowNodeStatus;
  variant?: "default" | "check";
}

interface ActionButtonProps {
  icon: ReactNode;
  label: string;
  color: string;
  onClick?: () => void;
  active?: boolean;
  disabled?: boolean;
}

function resolveImageSource(currentImage: string | undefined) {
  if (!currentImage) {
    return null;
  }
  if (
    currentImage.startsWith("data:image/") ||
    currentImage.startsWith("http://") ||
    currentImage.startsWith("https://")
  ) {
    return currentImage;
  }
  return `data:image/png;base64,${currentImage}`;
}

function resolveNodeStatusClass(status: FlowNodeStatus) {
  switch (status) {
    case "active":
      return "scale-110 border-indigo-500 bg-indigo-500/10 shadow-[0_0_20px_rgba(99,102,241,0.3)] text-indigo-400 z-20";
    case "completed":
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300 opacity-90";
    case "failed":
      return "border-rose-500/40 bg-rose-500/10 text-rose-300 opacity-90";
    case "attention":
      return "border-amber-500/40 bg-amber-500/10 text-amber-300 opacity-90";
    default:
      return "border-slate-800 bg-slate-900/50 opacity-40 grayscale";
  }
}

function determineFlowStatuses(
  eventFeed: FrontendRunStatePayload[],
  currentPhase: RunPhase | undefined,
): Record<FlowNodeId, FlowNodeStatus> {
  const statuses = Object.fromEntries(
    FLOW_SECTIONS.flatMap((section) => section.nodes.map((node) => [node.id, "idle"])),
  ) as Record<FlowNodeId, FlowNodeStatus>;

  for (const event of eventFeed) {
    const phase = event.phase as FlowNodeId;
    if (!(phase in statuses)) {
      continue;
    }
    if (event.event === "human_intervention_required") {
      statuses[phase] = "attention";
      continue;
    }
    if (event.event === "phase_failed") {
      statuses[phase] = "failed";
      continue;
    }
    if (event.event === "phase_completed" || event.event === "run_completed") {
      statuses[phase] = "completed";
      continue;
    }
    if (event.event === "phase_started" || event.event === "snapshot") {
      if (statuses[phase] === "idle") {
        statuses[phase] = "active";
      }
    }
  }

  if (currentPhase && currentPhase in statuses && statuses[currentPhase as FlowNodeId] === "idle") {
    statuses[currentPhase as FlowNodeId] = "active";
  }

  return statuses;
}

function renderTelemetryItems(robotState: Record<string, unknown> | undefined) {
  const jointPositions = Array.isArray(robotState?.joint_positions) ? robotState.joint_positions : [];
  const labels = [
    "Joint 1 (Base)",
    "Joint 2 (Arm)",
    "Joint 3 (Wrist)",
    "Joint 4",
    "Joint 5",
    "Joint 6",
  ];
  const items = labels.slice(0, Math.max(3, jointPositions.length)).map((label, index) => {
    const rawValue = jointPositions[index];
    const numericValue = typeof rawValue === "number" ? rawValue : null;
    return {
      label,
      val: numericValue == null ? "--" : `${numericValue.toFixed(2)}°`,
      status: Math.abs(numericValue ?? 0) > 85 ? "Warning" : "Normal",
    };
  });

  const graspState =
    typeof robotState?.grasp_state === "string"
      ? robotState.grasp_state
      : typeof robotState?.gripper === "string"
        ? robotState.gripper
        : "Unknown";

  return [
    ...items,
    {
      label: "Gripper",
      val: graspState,
      status: graspState.toLowerCase().includes("open") ? "Normal" : "Active",
    },
  ];
}

function formatLogLine(event: Record<string, unknown>) {
  const timestamp = typeof event.timestamp === "string" ? event.timestamp : "";
  const timeText = timestamp ? new Date(timestamp).toLocaleTimeString("zh-CN", { hour12: false }) : "--:--:--";
  const status = String(event.status || "INFO").toUpperCase();
  const message = String(event.message || "");
  return { timeText, status, message };
}

const Node = ({ id, label, status, variant = "default" }: NodeProps) => (
  <div
    data-node-id={id}
    className={`
      px-6 py-3 rounded-2xl border-2 transition-all duration-500 flex items-center gap-3
      ${resolveNodeStatusClass(status)}
    `}
  >
    {variant === "check" ? <CheckCircle2 size={18} /> : <Layers size={18} />}
    <span className="text-sm font-medium">{label}</span>
  </div>
);

const ActionButton = ({ icon, label, color, onClick, active = false, disabled = false }: ActionButtonProps) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    className={`
      flex flex-col items-center justify-center gap-2 p-4 rounded-2xl transition-all active:scale-95
      ${active ? "ring-2 ring-offset-2 ring-indigo-500 ring-offset-slate-950" : ""}
      ${color} text-white shadow-lg hover:brightness-110 disabled:opacity-50 disabled:hover:brightness-100
    `}
  >
    {icon}
    <span className="text-[10px] font-bold uppercase tracking-wider">{label}</span>
  </button>
);

export function App() {
  const initializedRef = useRef(false);
  const [darkMode, setDarkMode] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [videoStreamFailed, setVideoStreamFailed] = useState(false);

  const instruction = useWorkbenchStore((state) => state.instruction);
  const bootstrapStatus = useWorkbenchStore((state) => state.bootstrapStatus);
  const runStatus = useWorkbenchStore((state) => state.runStatus);
  const streamStatus = useWorkbenchStore((state) => state.streamStatus);
  const bootstrap = useWorkbenchStore((state) => state.bootstrap);
  const config = useWorkbenchStore((state) => state.config);
  const configDraft = useWorkbenchStore((state) => state.configDraft);
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const eventFeed = useWorkbenchStore((state) => state.eventFeed);
  const latestError = useWorkbenchStore((state) => state.latestError);
  const initialize = useWorkbenchStore((state) => state.initialize);
  const submitRun = useWorkbenchStore((state) => state.submitRun);
  const stopRun = useWorkbenchStore((state) => state.stopRun);
  const setInstruction = useWorkbenchStore((state) => state.setInstruction);
  const updateConfigDraft = useWorkbenchStore((state) => state.updateConfigDraft);
  const setActiveConfigTab = useWorkbenchStore((state) => state.setActiveConfigTab);

  useEffect(() => {
    if (initializedRef.current) {
      return;
    }
    initializedRef.current = true;
    void initialize();
  }, [initialize]);

  useEffect(() => {
    document.documentElement.style.colorScheme = darkMode ? "dark" : "light";
  }, [darkMode]);

  useEffect(() => {
    if (snapshot?.status === "running" || runStatus === "loading") {
      setIsRunning(true);
      return;
    }
    if (
      snapshot?.status === "completed" ||
      snapshot?.status === "failed" ||
      snapshot?.status === "cancelled"
    ) {
      setIsRunning(false);
    }
  }, [runStatus, snapshot?.status]);

  const imageSource = resolveImageSource(snapshot?.current_image);
  const videoStreamUrl = `${resolveRuntimeUrl("/api/v1/runtime/video-stream")}?fps=12&width=320&height=240&quality=50`;
  const telemetryItems = useMemo(() => renderTelemetryItems(snapshot?.robot_state), [snapshot?.robot_state]);
  const flowStatuses = useMemo(
    () => determineFlowStatuses(eventFeed, snapshot?.current_phase),
    [eventFeed, snapshot?.current_phase],
  );

  const activeSectionIndex = useMemo(() => {
    const index = FLOW_SECTIONS.findIndex((section) =>
      section.nodes.some((node) => flowStatuses[node.id] === "active"),
    );
    if (index !== -1) return index;

    // Fallback to current phase if no node is explicitly active in status
    if (snapshot?.current_phase) {
      const fallbackIndex = FLOW_SECTIONS.findIndex((section) =>
        section.nodes.some((node) => node.id === snapshot.current_phase),
      );
      if (fallbackIndex !== -1) return fallbackIndex;
    }
    return 0;
  }, [flowStatuses, snapshot?.current_phase]);

  const logs = useMemo(() => {
    if (eventFeed.length) {
      return eventFeed.slice(-12).map((event) =>
        formatLogLine({
          timestamp: event.timestamp,
          status: event.event,
          message: `${event.phase} · ${event.run.current_node || "-"} · ${event.run.error || event.run.assistant_response || "运行中"}`,
        }),
      );
    }
    if (snapshot?.logs?.length) {
      return snapshot.logs.slice(-12).map(formatLogLine);
    }
    return [
      { timeText: "--:--:--", status: "INFO", message: "等待任务启动。" },
      { timeText: "--:--:--", status: "PLAN", message: "等待后端返回规划结果。" },
      { timeText: "--:--:--", status: "EXEC", message: "等待执行阶段开始。" },
    ];
  }, [eventFeed, snapshot?.logs]);

  const currentTaskLabel = snapshot?.current_task || instruction || "等待任务输入";
  const assistantMessage = snapshot?.assistant_response || latestError || "等待 LLM 返回对话与动作决策。";
  const canSubmit = bootstrapStatus === "ready" && runStatus !== "loading";
  const canStop = snapshot?.status === "running" || isRunning;
  
  const resolvedConfig = configDraft || config || bootstrap?.config;

  const selectOptions = [
    resolvedConfig?.decision.model || "当前模型",
    "GPT-4o (Reasoning Mode)",
    "Claude 3.5 Sonnet",
    "Gemini 1.5 Pro",
    "Local: Llama-3-70B",
  ];

  const customModels = resolvedConfig?.frontend.custom_models || [];
  const visionOptions = useMemo(() => {
    const base = ["SmolVLA-0.1B", "Idefics3-8B-Llama", ...customModels.map((m) => m.id)];
    const current = resolvedConfig?.vision_model;
    const final = current && !base.includes(current) ? [current, ...base] : base;
    return [...final, "ADD_NEW_MODEL"];
  }, [resolvedConfig?.vision_model, customModels]);

  const currentVisionModel = resolvedConfig?.vision_model || visionOptions[0];

  return (
    <div
      className={`min-h-screen w-full transition-colors duration-300 ${darkMode ? "bg-slate-950 text-slate-100" : "bg-slate-50 text-slate-900"} p-4 font-sans`}
    >
      <header className="flex justify-between items-center mb-4 px-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Cpu size={20} className="text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight">
            OmniControl <span className="text-sm font-normal opacity-50">v2.0</span>
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => setDarkMode((value) => !value)}
            className="p-2 rounded-full hover:bg-slate-800 transition-colors"
          >
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <button
            type="button"
            className="p-2 rounded-full hover:bg-slate-800 transition-colors"
            onClick={() => setSettingsOpen(true)}
          >
            <Settings size={20} />
          </button>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-4 h-[calc(100vh-100px)] overflow-hidden">
        <div className="col-span-3 flex flex-col gap-4 h-full overflow-hidden">
          <div
            className={`relative overflow-hidden rounded-3xl border ${darkMode ? "border-slate-800 bg-slate-900" : "border-slate-200 bg-white"} aspect-video shadow-xl shrink-0`}
          >
            <div className="absolute top-3 left-3 z-10 flex items-center gap-2 bg-black/40 backdrop-blur-md px-2 py-1 rounded-full text-[10px] text-white">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              {imageSource ? "LIVE · FRONT_CAM" : "WAITING · FRONT_CAM"}
            </div>
            <div className="w-full h-full bg-slate-800 flex items-center justify-center relative">
              {!videoStreamFailed ? (
                <img
                  src={videoStreamUrl}
                  alt="front camera live stream"
                  className="w-full h-full object-cover"
                  onError={() => setVideoStreamFailed(true)}
                />
              ) : imageSource ? (
                <img src={imageSource} alt="front camera snapshot" className="w-full h-full object-cover" />
              ) : (
                <Video size={48} className="opacity-20" />
              )}
              <p className="absolute bottom-4 text-[10px] opacity-40 text-center w-full uppercase tracking-widest">
                Vision Feedback Stream
              </p>
            </div>
          </div>

          <div
            className={`flex-1 rounded-3xl border p-5 ${darkMode ? "border-slate-800 bg-slate-900/50" : "border-slate-200 bg-white"} shadow-lg overflow-y-auto no-scrollbar`}
          >
            <h3 className="text-sm font-semibold mb-4 flex items-center gap-2 sticky top-0 bg-inherit pb-2 z-10">
              <Activity size="16" className="text-indigo-500" /> 硬件遥测
            </h3>
            <div className="space-y-4">
              {telemetryItems.map((item) => (
                <div key={item.label} className="flex justify-between items-center border-b border-slate-800/50 pb-2">
                  <span className="text-xs opacity-60">{item.label}</span>
                  <div className="text-right">
                    <div className="text-sm font-mono">{item.val}</div>
                    <div className={`text-[10px] ${item.status === "Warning" ? "text-amber-500" : "text-emerald-500"}`}>{item.status}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-span-6 flex flex-col gap-4 h-full overflow-hidden">
          <div
            className={`flex-1 rounded-3xl border p-6 relative ${darkMode ? "border-slate-800 bg-slate-900/30" : "border-slate-200 bg-white"} shadow-2xl overflow-hidden flex flex-col`}
          >
            <div className="flex justify-between items-start mb-6 shrink-0">
              <div>
                <h2 className="text-lg font-bold">任务执行流</h2>
                <p className="text-xs opacity-50">LangGraph 实时逻辑拓扑</p>
              </div>
              <div className="px-3 py-1 bg-indigo-500/10 text-indigo-500 rounded-full text-xs font-medium border border-indigo-500/20">
                当前任务: {currentTaskLabel}
              </div>
            </div>

            <div className="flex-1 flex flex-col justify-center items-center relative z-10">
              {/* 层级切换指示器 */}
              <div className="flex gap-2 mb-8 bg-slate-900/40 p-1.5 rounded-full border border-slate-800/50">
                {FLOW_SECTIONS.map((section, idx) => (
                  <div
                    key={section.title}
                    className={`w-2 h-2 rounded-full transition-all duration-300 ${idx === activeSectionIndex ? "w-6 bg-indigo-500" : "bg-slate-700"}`}
                  />
                ))}
              </div>

              <div 
                key={activeSectionIndex}
                className="w-full flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-700"
              >
                <div className="mb-4 text-[12px] uppercase tracking-[0.3em] text-indigo-400 font-black flex items-center gap-2">
                  <Layers size={14} className="animate-pulse" />
                  {FLOW_SECTIONS[activeSectionIndex].title}
                </div>
                
                <div className="flex flex-wrap justify-center items-center gap-6 p-8 rounded-[40px] border border-indigo-500/20 bg-indigo-500/5 backdrop-blur-md shadow-[0_0_50px_rgba(99,102,241,0.1)] relative group">
                  <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-[40px] blur opacity-25 group-hover:opacity-40 transition duration-1000"></div>
                  {FLOW_SECTIONS[activeSectionIndex].nodes.map((node, nodeIndex) => (
                    <div key={node.id} className="flex items-center gap-6 relative z-10">
                      <Node
                        id={node.id}
                        label={node.label}
                        status={flowStatuses[node.id]}
                        variant={node.variant}
                      />
                      {nodeIndex < FLOW_SECTIONS[activeSectionIndex].nodes.length - 1 ? (
                        <ChevronRight className={`transition-opacity duration-500 ${flowStatuses[node.id] === 'completed' ? 'opacity-80 text-emerald-400' : 'opacity-20 text-slate-400'}`} />
                      ) : null}
                    </div>
                  ))}
                </div>

                <div className="mt-8 text-center max-w-md">
                  <p className="text-[11px] text-slate-400 leading-relaxed italic">
                    {activeSectionIndex === 0 && "感知环境并解析您的指令。"}
                    {activeSectionIndex === 1 && "正在为您规划最优操作路径。"}
                    {activeSectionIndex === 2 && "精准控制机械臂完成物理交互。"}
                    {activeSectionIndex === 3 && "诊断异常并执行自动补偿策略。"}
                    {activeSectionIndex === 4 && "更新记忆并验证最终任务状态。"}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-auto pt-4 shrink-0">
              <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 px-4 py-3 text-sm text-indigo-100 transition-all duration-300">
                <div className="text-[10px] uppercase tracking-widest opacity-60 mb-1 flex items-center gap-1">
                  <Mic size={10} className="text-indigo-400" /> Assistant Response
                </div>
                <div className="font-medium line-clamp-2">{assistantMessage}</div>
              </div>
            </div>

            <div className="absolute inset-0 opacity-[0.03] pointer-events-none uppercase font-black text-[120px] break-all leading-none select-none">
              Logic Graph Workflow Robot Control
            </div>
          </div>

          <div
            className={`h-32 rounded-3xl border p-4 font-mono text-[11px] overflow-y-auto no-scrollbar shrink-0 ${darkMode ? "border-slate-800 bg-black/40 text-emerald-500/80" : "border-slate-200 bg-slate-100 text-slate-700"}`}
          >
            {logs.map((log, index) => (
              <div key={`${log.timeText}-${log.status}-${index}`} className={index === logs.length - 1 && isRunning ? "animate-pulse" : ""}>
                [{log.timeText}] <span className="text-indigo-400">{log.status}:</span> {log.message}
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-3 flex flex-col gap-4 h-full overflow-hidden">
          <div
            className={`flex-1 rounded-3xl border p-6 ${darkMode ? "border-slate-800 bg-slate-900/50" : "border-slate-200 bg-white"} shadow-lg flex flex-col overflow-hidden`}
          >
            <h3 className="text-sm font-semibold mb-6 shrink-0">交互控制中心</h3>

            <div
              className={`rounded-2xl p-4 mb-6 ${darkMode ? "bg-slate-950" : "bg-slate-50"} border border-slate-800/50 shrink-0`}
            >
              <div className="flex justify-between items-center mb-3">
                <span className="text-[10px] opacity-40 uppercase tracking-tighter">Command Input</span>
                <Mic size={14} className={`text-indigo-500 ${isRunning ? 'animate-bounce' : ''}`} />
              </div>
              <input
                type="text"
                value={instruction}
                onChange={(event) => setInstruction(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && canSubmit) {
                    void submitRun();
                    setIsRunning(true);
                  }
                }}
                placeholder="输入指令，如：‘帮我把方块拿过来’"
                className="bg-transparent w-full border-none focus:outline-none text-sm"
              />
              <div className="flex justify-end mt-2">
                <button
                  type="button"
                  disabled={!canSubmit}
                  onClick={() => {
                    void submitRun();
                    setIsRunning(true);
                  }}
                  className="p-2 bg-indigo-600 rounded-lg hover:bg-indigo-500 transition-all disabled:opacity-50"
                >
                  <Send size={14} className="text-white" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-6 shrink-0">
              <ActionButton
                icon={<Play size={18} />}
                label="开始"
                color="bg-emerald-600"
                onClick={() => {
                  void submitRun();
                  setIsRunning(true);
                }}
                active={isRunning}
                disabled={!canSubmit}
              />
              <ActionButton
                icon={<Square size={18} />}
                label="结束"
                color="bg-slate-700"
                onClick={() => void stopRun()}
                disabled={!canStop}
              />
            </div>

            <div className="mt-auto pt-6 border-t border-slate-800/50 shrink-0">
              <label className="text-[11px] font-bold text-indigo-400 uppercase mb-4 block">模型配置</label>
              
              <div className="space-y-4">
                <div>
                  <label className="text-[10px] opacity-40 uppercase mb-2 block">视觉模型配置</label>
                  <select
                    className={`w-full text-xs p-2 rounded-xl border ${darkMode ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200"}`}
                    value={currentVisionModel}
                    onChange={(e) => {
                      if (e.target.value === "ADD_NEW_MODEL") {
                        setActiveConfigTab("custom_models");
                        setSettingsOpen(true);
                      } else {
                        updateConfigDraft("root", "vision_model", e.target.value);
                      }
                    }}
                  >
                    {visionOptions.map((option) => (
                      <option key={option} value={option}>
                        {option === "ADD_NEW_MODEL" ? "+ 添加新模型..." : option}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] opacity-40 uppercase mb-2 block">决策引擎配置</label>
                  <select
                    className={`w-full text-xs p-2 rounded-xl border ${darkMode ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200"}`}
                    value={selectOptions[0]}
                    onChange={(e) => updateConfigDraft("decision", "model", e.target.value)}
                  >
                    {selectOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between px-1">
                <span className="text-[10px] opacity-60">Runtime 状态</span>
                <span className="text-[10px] text-emerald-500 font-mono">{snapshot?.status || streamStatus || "idle"}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
