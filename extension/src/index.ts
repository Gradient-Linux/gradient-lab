import { JupyterFrontEnd, JupyterFrontEndPlugin } from "@jupyterlab/application";
import { Widget } from "@lumino/widgets";

import { REFRESH_INTERVAL_MS, fetchGradientLabStatus, type GradientLabStatus, visibleActionsForRole } from "./status";

class GradientLabSidebar extends Widget {
  private refreshHandle: number | null = null;
  private latestStatus: GradientLabStatus | null = null;

  constructor() {
    super({ node: document.createElement("section") });
    this.addClass("jp-GradientLabSidebar");
    this.title.label = "Gradient Lab";
    this.title.closable = false;
    this.node.className = "jp-GradientLabSidebar";
    this.node.style.padding = "12px";
    this.node.style.display = "flex";
    this.node.style.flexDirection = "column";
    this.node.style.gap = "12px";
    this.node.style.fontFamily = '"IBM Plex Sans", "Noto Sans", system-ui, sans-serif';
    this.node.style.fontSize = "13px";
    this.node.style.lineHeight = "1.45";
  }

  async start(): Promise<void> {
    await this.refresh();
    this.refreshHandle = window.setInterval(() => void this.refresh(), REFRESH_INTERVAL_MS);
  }

  async refresh(): Promise<void> {
    try {
      this.latestStatus = await fetchGradientLabStatus();
      this.render();
    } catch (error) {
      const message = error instanceof Error ? error.message : "unknown error";
      this.render(message);
    }
  }

  private render(errorMessage?: string): void {
    const status = this.latestStatus;
    const actions = visibleActionsForRole(status?.role);
    const resolverMessage = errorMessage ?? this.describeResolver(status?.resolver);
    const quota = status?.quota;

    this.node.innerHTML = `
      <div style="display:grid;gap:10px;">
        <header>
          <div style="font-size:16px;font-weight:700;letter-spacing:0.02em;">Gradient Lab</div>
          <div style="color:var(--jp-ui-font-color2,#667085);">Notebook collaboration status</div>
        </header>
        <section>
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:var(--jp-ui-font-color2,#667085);">Resolver</div>
          <div>${this.escape(resolverMessage)}</div>
        </section>
        <section>
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:var(--jp-ui-font-color2,#667085);">Quota</div>
          <div>${this.describeQuota(quota)}</div>
        </section>
        <section>
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:var(--jp-ui-font-color2,#667085);">Actions</div>
          <ul style="padding-left:18px;margin:0;display:grid;gap:4px;">
            ${actions.map((action) => `<li><strong>${this.escape(action.label)}</strong></li>`).join("")}
          </ul>
          ${status?.role === "gradient-developer" ? '<div style="margin-top:6px;color:var(--jp-ui-font-color2,#667085);">Operator-only actions are hidden for developer users.</div>' : ""}
        </section>
        <footer style="color:var(--jp-ui-font-color2,#667085);font-size:11px;">
          <div>Group: ${this.escape(status?.group || quota?.group || "unassigned")}</div>
          <div>Role: ${this.escape(status?.role || "gradient-viewer")}</div>
          <div>Refreshed: ${this.escape(status?.refreshed_at || new Date().toISOString())}</div>
        </footer>
      </div>
    `;
  }

  private describeResolver(resolver: GradientLabStatus["resolver"] | undefined): string {
    if (!resolver) {
      return "Resolver data unavailable";
    }
    if (resolver.available === false) {
      return resolver.error || resolver.message || "Resolver unavailable";
    }
    if (typeof resolver.message === "string" && resolver.message) {
      return resolver.message;
    }
    if (resolver.error) {
      return resolver.error;
    }
    return "Resolver available";
  }

  private describeQuota(quota: GradientLabStatus["quota"] | undefined): string {
    if (!quota) {
      return "Quota data unavailable";
    }
    const parts: string[] = [];
    if (quota.group) {
      parts.push(`Group ${this.escape(quota.group)}`);
    }
    if (typeof quota.cpu_cores === "number") {
      parts.push(`CPU ${quota.cpu_cores} cores`);
    }
    if (typeof quota.memory_gb === "number") {
      parts.push(`Memory ${quota.memory_gb} GB`);
    }
    if (typeof quota.gpu_count === "number") {
      parts.push(`GPU ${quota.gpu_count}`);
    }
    if (parts.length === 0) {
      return "No quota metadata reported";
    }
    return parts.join(" · ");
  }

  private escape(value: string): string {
    return value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  override dispose(): void {
    if (this.refreshHandle !== null) {
      window.clearInterval(this.refreshHandle);
      this.refreshHandle = null;
    }
    super.dispose();
  }
}

const plugin: JupyterFrontEndPlugin<void> = {
  id: "@gradient-linux/gradient-lab:sidebar",
  autoStart: true,
  activate: async (app: JupyterFrontEnd) => {
    const sidebar = new GradientLabSidebar();
    app.shell.add(sidebar, "left", { rank: 900 });
    await sidebar.start();
  }
};

export default plugin;
