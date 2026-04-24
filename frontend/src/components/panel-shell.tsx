import type { PropsWithChildren, ReactNode } from "react";

interface PanelShellProps extends PropsWithChildren {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
  compact?: boolean;
}

export function PanelShell({
  title,
  subtitle,
  actions,
  className,
  compact = false,
  children,
}: PanelShellProps) {
  return (
    <section className={["panel-shell", compact ? "panel-shell--compact" : "", className || ""].filter(Boolean).join(" ")}>
      <header className="panel-shell__header">
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {actions ? <div className="panel-shell__actions">{actions}</div> : null}
      </header>
      <div className="panel-shell__body">{children}</div>
    </section>
  );
}
