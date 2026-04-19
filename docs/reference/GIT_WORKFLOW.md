# Git 管理参考

## 文档定位

本文档定义项目推荐 Git 工作方式，目标是让多 Agent 协作开发、文档维护和实验记录保持可追踪、可回退、可交接。

## 一、分支策略

推荐分支：
- `main`：稳定版本，保持可展示、可交付
- `dev`：日常集成分支
- `feature/*`：功能开发分支
- `docs/*`：文档维护分支
- `experiment/*`：实验与验证分支
- `fix/*`：缺陷修复分支

分支建议：
- 未完成的大功能不要直接进入 `main`
- 文档结构重构和大规模补文档，优先使用 `docs/*`
- 实验性动作、临时验证和数据分析，优先使用 `experiment/*`

## 二、提交规范

提交原则：
- 一次提交聚焦单一主题
- 代码与对应文档尽量同批提交
- 大改动前先保证 `HANDOFF` 和 `DEVELOPMENT_LOG` 可更新

推荐提交前缀：
- `feat:` 新功能
- `fix:` 缺陷修复
- `docs:` 文档更新
- `refactor:` 结构调整
- `test:` 测试相关
- `chore:` 杂项维护

提交信息示例：
- `docs: restructure docs into specs reference and records`
- `feat: add scene_analyzer mcp integration`
- `test: add verifier loop path checks`

## 三、合并前检查

合并前至少确认：
- 与需求文档一致
- 与 `spec` 一致
- 影响接口时已更新 `docs/reference/INTERFACES.md`
- 影响架构时已更新 `docs/reference/ARCHITECTURE.md`
- 已更新 `docs/records/DEVELOPMENT_LOG.md`
- 已更新 `docs/records/HANDOFF.md`
- 需要时已补充 `docs/records/TEST_REPORT.md`

## 四、里程碑标记

建议在以下节点打 tag：
- 第一阶段骨架完成
- 第二阶段 LangGraph 主流程完成
- 第三阶段前端与工具集成完成
- 第四阶段闭环验证与论文材料完成

推荐 tag 风格：
- `v0.1-stage1`
- `v0.2-stage2`
- `v0.3-stage3`
- `v1.0-defense`

## 五、冲突处理原则

出现冲突时按以下顺序判断：
1. 先核对需求文档
2. 再核对 `DEVELOPMENT_SPEC.md`
3. 再核对 `docs/specs/`
4. 再核对 `docs/reference/`
5. 最后修正代码和 `docs/records/`

## 六、当前适用状态

当前项目仍处于文档基线完善和开发准备阶段，Git 重点应放在：
- 保持文档结构清晰
- 保持架构、接口与交接材料同步
- 为后续代码开发留下清楚的提交轨迹
