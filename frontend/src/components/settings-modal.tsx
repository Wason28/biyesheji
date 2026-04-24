import { ConfigPanel } from "./config-panel";
import { ToolsPanel } from "./tools-panel";

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsModal({ open, onClose }: SettingsModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="settings-modal" role="dialog" aria-modal="true" aria-label="系统设置">
      <button type="button" className="settings-modal__backdrop" aria-label="关闭设置" onClick={onClose} />
      <div className="settings-modal__panel">
        <header className="settings-modal__header">
          <div>
            <p className="brand-kicker">System Settings</p>
            <h2>系统设置</h2>
          </div>
          <button type="button" className="icon-button button-secondary" onClick={onClose}>
            关闭
          </button>
        </header>
        <div className="settings-modal__content">
          <ConfigPanel embedded />
          <ToolsPanel embedded />
        </div>
      </div>
    </div>
  );
}
