import { expect, test } from "@playwright/test";

test("workbench bootstraps and renders a completed run", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("app-shell")).toBeVisible();
  await expect(page.getByTestId("phase-flow-panel")).toBeVisible();
  await expect(page.getByTestId("event-log-panel")).toBeVisible();
  await expect(page.getByTestId("control-panel")).toBeVisible();

  const instructionInput = page.getByTestId("instruction-input");
  await expect(instructionInput).toBeVisible();
  await instructionInput.fill("抓取桌面方块");

  const startButton = page.getByTestId("start-run-button");
  await expect(startButton).toBeEnabled();

  await startButton.click();

  await expect(page.getByTestId("run-status-panel")).toContainText(/Run ID:/);
  await expect(page.getByTestId("run-status-panel")).toContainText(/Task: .*抓取桌面方块/);

  await expect(page.getByTestId("event-log-panel")).not.toContainText("等待任务提交");
  await expect(page.getByTestId("event-log-panel")).toContainText(/PHASE_STARTED|PHASE_COMPLETED|RUN_COMPLETED/);

  await expect(page.getByTestId("node-perceive")).toHaveAttribute("data-state", /active|done/);
  await expect(page.getByTestId("node-plan")).toHaveAttribute("data-state", /active|done/);
  await expect(page.getByTestId("node-execute")).toHaveAttribute("data-state", /active|done|failed/);
  await expect(page.getByTestId("node-verify")).toHaveAttribute("data-state", /active|done|failed/);

  await expect(page.getByTestId("run-status-panel")).toContainText(/已完成|失败|运行中/);

  await expect.poll(async () => {
    return (await page.getByTestId("run-status-panel").textContent()) || "";
  }).toMatch(/已完成|失败/);
});


test("settings modal refreshes tools and saves config", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "打开设置" }).click();
  const dialog = page.getByRole("dialog", { name: "系统设置" });

  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("button", { name: "刷新配置" })).toBeVisible();

  await dialog.getByRole("button", { name: "刷新工具" }).click();
  await expect(dialog).toContainText(/工具列表已刷新，当前共 \d+ 项。/);

  await dialog.getByRole("button", { name: "显示助手" }).click();
  await expect(dialog).toContainText("模型部署助手");

  await dialog.getByRole("button", { name: "保存配置" }).click();
  await expect(dialog).toContainText("配置已提交并与后端完成同步。");
});


test("control panel validates empty instruction locally", async ({ page }) => {
  await page.goto("/");

  const startButton = page.getByTestId("start-run-button");
  await expect(startButton).toBeEnabled();
  await startButton.click();

  await expect(page.getByTestId("control-panel")).toContainText("请输入任务指令后再启动。");
});
