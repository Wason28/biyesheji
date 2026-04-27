import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";

export function DialoguePanel() {
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const instruction = useWorkbenchStore((state) => state.instruction);

  const userText = snapshot?.user_instruction || instruction || "等待输入任务指令。";
  const assistantText =
    snapshot?.assistant_response ||
    "我会结合当前画面、机器人状态和任务目标，先给出一句自然语言回复，再选择动作执行。";

  return (
    <PanelShell
      title="任务对话"
      subtitle="LLM 不只给 tool call，也会返回面向用户的自然语言回复。"
      compact
    >
      <div className="dialogue-thread">
        <article className="chat-bubble chat-bubble--user">
          <span className="chat-bubble__role">你</span>
          <strong>{userText}</strong>
          <small>instruction</small>
        </article>
        <article className="chat-bubble chat-bubble--assistant">
          <span className="chat-bubble__role">智能体</span>
          <strong>{assistantText}</strong>
          <small>
            {snapshot?.current_phase || "bootstrap"} · {snapshot?.selected_action || "waiting"}
          </small>
        </article>
      </div>
    </PanelShell>
  );
}
