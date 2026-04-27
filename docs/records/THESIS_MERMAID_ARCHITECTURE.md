# 论文架构设计图 Mermaid 稿

本文档汇总毕业论文可直接使用的 Mermaid 架构图，严格按当前项目真实实现整理，不额外虚构未落地模块。

## 建议纳入论文的图

1. 系统总体架构图
2. 三层解耦与统一装配关系图
3. 前后端运行时通信图
4. `run_id` 生命周期时序图
5. 决策层 LangGraph 状态流图
6. 感知-决策-执行工具调用图
7. 执行层安全闭环图
8. 前端工作台状态管理与接口接线图
9. 感知层单层架构图
10. 决策层单层架构图
11. 执行层单层架构图
12. 汉诺塔任务 Skill 流程图

---

## 1. 系统总体架构图

建议放置章节：第 3 章 系统总体架构设计

```mermaid
flowchart LR
    U[用户 / 实验人员]
    FE[前端工作台<br/>React + TypeScript + Zustand]
    BE[后端运行时门面<br/>FrontendRuntimeFacade + HTTP]
    RT[统一运行时装配<br/>Phase1Runtime]

    subgraph Core[具身智能核心链路]
        P[感知层<br/>Camera + Robot State + VLM]
        D[决策层<br/>LangGraph Decision Engine]
        E[执行层<br/>Execution Runtime + Robot Adapter]
    end

    subgraph Model[模型与设备资源]
        LLM[LLM Provider<br/>OpenAI / MiniMax / Ollama]
        VLM[VLM Provider<br/>MiniMax-VL / GPT-4o Vision / Ollama Vision]
        CAM[摄像头]
        ARM[机械臂 / 夹爪]
    end

    U --> FE
    FE --> BE
    BE --> RT
    RT --> P
    RT --> D
    RT --> E

    P --> CAM
    P --> VLM
    D --> LLM
    E --> ARM

    D -->|调用感知工具| P
    D -->|调用执行工具| E
    E -->|执行反馈| D
    P -->|场景理解 / 状态| D
    BE -->|快照 / 事件 / 配置 / 视频流| FE
```

---

## 2. 三层解耦与统一装配关系图

建议放置章节：第 3 章 系统总体架构设计

```mermaid
flowchart TB
    CFG[配置文件 AppConfig]
    APP[build_runtime / build_frontend_facade]
    MCP[UnifiedMCPClient]

    subgraph Frontend[前端层]
        WB[Workbench]
    end

    subgraph Backend[后端门面层]
        HTTP[BackendHTTPApp]
        FACADE[FrontendRuntimeFacade]
        REG[RunRegistry]
    end

    subgraph Core[三层核心]
        P[感知层<br/>PerceptionMCPServer]
        D[决策层<br/>DecisionEngine]
        E[执行层<br/>MockMCPServer / ExecutionRuntime]
    end

    CFG --> APP
    APP --> P
    APP --> E
    APP --> MCP
    APP --> D

    P --> MCP
    E --> MCP
    MCP --> D

    WB --> HTTP
    HTTP --> FACADE
    FACADE --> REG
    FACADE --> P
    FACADE --> D
    FACADE --> E
```

---

## 3. 前后端运行时通信图

建议放置章节：第 7 章 前端工作台设计与实现

```mermaid
flowchart LR
    FE[前端 Workbench Store]
    API[frontend/src/lib/api.ts]
    SSE[frontend/src/lib/sse.ts]
    HTTP[BackendHTTPApp]
    FACADE[FrontendRuntimeFacade]
    RUN[RunRegistry]
    MJPEG[iter_video_stream]

    FE -->|GET /api/v1/runtime/bootstrap| API
    FE -->|GET /api/v1/runtime/config| API
    FE -->|PUT /api/v1/runtime/config| API
    FE -->|GET /api/v1/runtime/tools| API
    FE -->|POST /api/v1/runtime/tools/refresh| API
    FE -->|POST /api/v1/runtime/runs| API
    FE -->|GET snapshot_url| API
    FE -->|POST snapshot_url/stop| API
    FE -->|GET events_url| SSE
    FE -->|GET /api/v1/runtime/video-stream| MJPEG

    API --> HTTP
    SSE --> HTTP
    MJPEG --> HTTP
    HTTP --> FACADE
    FACADE --> RUN
```

---

## 4. `run_id` 生命周期时序图

建议放置章节：第 7 章 前后端通信机制

```mermaid
sequenceDiagram
    participant User as 用户
    participant FE as 前端 Workbench
    participant HTTP as BackendHTTPApp
    participant Facade as FrontendRuntimeFacade
    participant Registry as RunRegistry
    participant Worker as Run Worker Thread

    User->>FE: 输入自然语言指令
    FE->>HTTP: POST /api/v1/runtime/runs
    HTTP->>Facade: start_run(instruction, run_id?)
    Facade->>Registry: create_session(run_id)
    Facade->>Registry: publish(version=1, event=snapshot)
    Facade->>Worker: 启动后台线程
    Facade-->>FE: 202 Accepted<br/>snapshot_url + events_url + accepted.run

    FE->>HTTP: GET events_url
    HTTP->>Facade: iter_run_events(run_id, after_version)
    Facade->>Registry: 读取新事件
    Registry-->>FE: SSE phase_started / phase_completed / run_completed

    alt SSE 中断或补偿同步
        FE->>HTTP: GET snapshot_url
        HTTP->>Facade: get_run(run_id)
        Facade->>Registry: latest(run_id)
        Registry-->>FE: 当前最新快照
    end

    alt 用户主动结束
        FE->>HTTP: POST snapshot_url/stop
        HTTP->>Facade: stop_run(run_id)
        Facade->>Registry: request_stop + publish(run_completed)
        Registry-->>FE: terminal=true
    end
```

---

## 5. 决策层 LangGraph 状态流图

建议放置章节：第 5 章 决策层 Agent 设计与实现

```mermaid
flowchart TD
    trigger[trigger<br/>交互触发与指令采集]
    nlu[nlu<br/>语义解析与目标提取]
    sensory[sensory<br/>环境感知]
    assessment[assessment<br/>置信度评估]
    ap[active_perception<br/>主动感知增强]
    plan[task_planning<br/>任务规划]
    pre[pre_feedback<br/>执行前反馈]
    motion[motion_control<br/>动作执行]
    verify[verification<br/>结果验证]
    err[error_diagnosis<br/>错误诊断]
    hri[hri<br/>人工干预判断]
    comp[compensation<br/>补偿控制]
    success[success_notice<br/>完成信号反馈]
    goal[goal_check<br/>目标完成判断]
    memory[state_compression<br/>状态压缩与记忆更新]
    final[final_status<br/>终态报告]

    trigger --> nlu --> sensory --> assessment
    assessment -->|置信度不足| ap
    ap --> sensory
    assessment -->|置信度可接受| plan
    plan -->|规划成功| pre
    plan -->|规划失败| final
    pre --> motion --> verify
    verify -->|失败| err
    verify -->|成功| success
    err --> hri --> comp --> motion
    success --> goal
    goal -->|任务完成| final
    goal -->|仍有子任务| memory --> sensory
```

---

## 6. 感知-决策-执行工具调用图

建议放置章节：第 3 章 架构设计 或 第 5 章 决策层实现

```mermaid
flowchart LR
    D[DecisionEngine]
    MCP[UnifiedMCPClient]

    subgraph P[感知工具]
        GI[get_image]
        GS[get_robot_state]
        DS[describe_scene]
    end

    subgraph E[执行工具]
        MT[move_to]
        MH[move_home]
        GR[grasp]
        SR[servo_rotate]
        RL[release]
        CE[clear_emergency_stop]
        SV[run_smolvla]
    end

    D --> MCP
    MCP --> GI
    MCP --> GS
    MCP --> DS
    MCP --> MT
    MCP --> MH
    MCP --> GR
    MCP --> SR
    MCP --> RL
    MCP --> CE
    MCP --> SV

    GI --> D
    GS --> D
    DS --> D
    MT --> D
    MH --> D
    GR --> D
    SR --> D
    RL --> D
    CE --> D
    SV --> D
```

---

## 7. 执行层安全闭环图

建议放置章节：第 6 章 动作执行层设计与实现

```mermaid
flowchart TD
    Req[动作请求]
    Runtime[ExecutionRuntime]
    Precheck[安全前置检查<br/>连接 / 心跳 / 急停 / 遥测]
    ActionCheck[动作级检查<br/>位移阈值 / 奇异点 / 力控 / 舵机角度]
    Adapter[RobotAdapter]
    Robot[机械臂 / 夹爪]
    Telemetry[运行后遥测]
    Safe[遥测安全校验<br/>温度 / 电流 / 位置误差]
    Result[执行结果与日志]
    Stop[拒绝执行 / 急停锁定]

    Req --> Runtime --> Precheck
    Precheck -->|失败| Stop
    Precheck -->|通过| ActionCheck
    ActionCheck -->|失败| Stop
    ActionCheck -->|通过| Adapter --> Robot
    Robot --> Telemetry --> Safe
    Safe -->|失败| Stop
    Safe -->|通过| Result
```

---

## 8. 前端工作台状态管理与接口接线图

建议放置章节：第 7 章 前端工作台设计与实现

```mermaid
flowchart TB
    App[App.tsx / 组件树]
    Store[useWorkbenchStore]

    subgraph Panels[界面面板]
        CP[控制区 Control Panel]
        RP[实时画面 Runtime Panel]
        EP[事件流 Event Panel]
        DP[对话区 Dialogue Panel]
        TP[工具面板 Tools Panel]
        CFG[配置面板 Config Panel]
    end

    subgraph Actions[核心动作]
        Init[initialize]
        Submit[submitRun]
        Sync[syncRunSnapshot]
        Stop[stopRun]
        Save[saveConfigDraft]
        Refresh[refreshConfig / refreshTools]
    end

    subgraph IO[接口层]
        API[api.ts]
        ES[sse.ts]
    end

    App --> CP
    App --> RP
    App --> EP
    App --> DP
    App --> TP
    App --> CFG

    CP --> Store
    RP --> Store
    EP --> Store
    DP --> Store
    TP --> Store
    CFG --> Store

    Store --> Init
    Store --> Submit
    Store --> Sync
    Store --> Stop
    Store --> Save
    Store --> Refresh

    Init --> API
    Submit --> API
    Submit --> ES
    Sync --> API
    Stop --> API
    Save --> API
    Refresh --> API
```

---

## 9. 感知层单层架构图

建议放置章节：第 4 章 环境感知层设计

```mermaid
flowchart LR
    subgraph Input[输入源]
        CAM[CameraAdapter<br/>真实摄像头 / Mock Camera]
        RS[RobotStateAdapter<br/>真实状态 / Mock State]
    end

    subgraph Perception[感知运行时]
        PS[PerceptionMCPServer]
        GI[get_image]
        GS[get_robot_state]
        DS[describe_scene]
    end

    subgraph Vision[视觉理解]
        VLM[BaseVLMProvider<br/>MiniMax / GPT-4o / Ollama]
        SC[结构化场景输出<br/>scene_description + observations + confidence]
    end

    CAM --> GI
    RS --> GS
    PS --> GI
    PS --> GS
    PS --> DS
    GI --> DS
    DS --> VLM --> SC
    GS --> SC
    SC --> OUT[统一感知合同输出]
```

---

## 10. 决策层单层架构图

建议放置章节：第 5 章 决策层 Agent 设计与实现

```mermaid
flowchart TD
    IN[用户自然语言指令]
    STATE[DecisionAgentState]
    GRAPH[LangGraph Decision Graph]
    LLM[Decision Provider<br/>OpenAI / MiniMax / Ollama / Heuristic Fallback]
    MCP[UnifiedMCPClient]

    subgraph Nodes[核心节点]
        T[trigger]
        N[nlu]
        S[sensory]
        A[assessment]
        AP[active_perception]
        P[task_planning]
        PF[pre_feedback]
        M[motion_control]
        V[verification]
        ED[error_diagnosis]
        H[hri]
        C[compensation]
        G[goal_check]
        F[final_status]
    end

    IN --> STATE
    STATE --> GRAPH
    GRAPH --> T --> N --> S --> A
    A --> AP
    AP --> S
    A --> P
    P --> LLM
    P --> PF --> M --> V
    V -->|失败| ED --> H --> C --> M
    V -->|成功| G --> F
    GRAPH <--> MCP
    GRAPH --> STATE
    F --> OUT[终态报告 / assistant_response / final_report]
```

---

## 11. 执行层单层架构图

建议放置章节：第 6 章 动作执行层设计与实现

```mermaid
flowchart LR
    subgraph Request[上层调用]
        MCPReq[MCP Tool Request]
    end

    subgraph Runtime[执行运行时]
        Server[MockMCPServer]
        ER[ExecutionRuntime]
        Safety[SafetyManager]
        Validator[参数校验器]
        Smol[SmolVLA Planner]
    end

    subgraph Tools[执行工具]
        MT[move_to]
        MH[move_home]
        GR[grasp]
        SR[servo_rotate]
        RL[release]
        CE[clear_emergency_stop]
        SV[run_smolvla]
    end

    subgraph Hardware[底层执行]
        AD[RobotAdapter]
        HW[机械臂 / 夹爪 / 舵机]
        TEL[遥测反馈]
    end

    MCPReq --> Server --> ER
    ER --> Validator
    ER --> Safety
    ER --> MT
    ER --> MH
    ER --> GR
    ER --> SR
    ER --> RL
    ER --> CE
    ER --> SV
    SV --> Smol
    Smol --> MT
    Smol --> MH
    Smol --> GR
    Smol --> RL

    MT --> AD
    MH --> AD
    GR --> AD
    SR --> AD
    RL --> AD
    CE --> AD
    AD --> HW --> TEL --> Safety
    Safety --> OUT[执行结果 / 日志 / 安全边界]
```

---

## 12. 汉诺塔任务 Skill 流程图

建议放置章节：任务技能扩展小节 / 附录

```mermaid
flowchart TD
    Goal[用户提出汉诺塔目标]
    Detect[指令识别<br/>looks_like_hanoi_instruction]
    Problem[结构化问题<br/>source / target / auxiliary / num_disks]
    Rules[合法约束<br/>一次一环 / 大环不能压小环]
    Recursion[递归求解<br/>solve_hanoi]
    Moves[步骤序列<br/>HanoiMove 列表]
    Prompt[中文原子提示词<br/>render_hanoi_move_prompt]
    Card[Skill Card<br/>Prompt + Constraints + Steps]
    Future[后续可映射到<br/>LangGraph / 机械臂动作]

    Goal --> Detect --> Problem --> Rules --> Recursion --> Moves --> Prompt --> Card --> Future
```

---

## 使用建议

- 第 3 章优先放图 1、图 2、图 6。
- 第 4 章优先放图 9。
- 第 5 章优先放图 5、图 10。
- 第 6 章优先放图 7、图 11。
- 第 7 章优先放图 3、图 4、图 8。
- 任务技能扩展或附录可放图 12。
- 如果答辩页数有限，保留图 1、图 4、图 5、图 7 四张即可。
