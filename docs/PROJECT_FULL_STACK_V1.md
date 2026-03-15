# Project: full-stack-v1 — 全功能测试

> 目标: 在本地 workspace 中运行完整的多 Agent 系统, 端到端验证所有组件协作

## 系统拓扑

```
                     ┌── example-frontend (Gradio 监控) ──┐
                     │                                     │
 ┌─── [daemon] ──────┼── agent_node_1 ──┐                  │
 │    19999          │── agent_node_2 ──┤                  │
 │                   │                  │                  │
 │    Topics:        │                  ▼                  │
 │    /chat/*        │          TagentacleMCPServer        │
 │    /memory/*      │          (subscribe/publish/        │
 │    /mcp/directory │           read_mailbox via MCP)     │
 │                   │                  │                  │
 │                   │                  ▼                  │
 │    Services:      │     ┌── shell-server (MCP) ──┐     │
 │    /inference/chat│     │── example-mcp-server ──│     │
 │    /memory/load   │     │── mock-external (MCP) ─│     │
 │    /memory/list   │     └────────────────────────┘     │
 │                   │                                     │
 │                   ├── example-inference                  │
 │                   ├── example-memory                     │
 │                   ├── container-orchestrator              │
 │                   └── mcp-gateway (relay mock-external)  │
 └────────────────────────────────────────────────────────┘
                     │
                  example-bringup (编排所有上述节点)
```

## 涉及仓库 & Issue 索引

| 仓库 | Issue | 标题 | Phase | 决议 |
|------|-------|------|-------|------|
| example-agent | [#1](example-agent/refactor-mailbox-agent-node_1.md) | refactor: AgentNode 邮箱架构 | 2 | — |
| example-agent | [#2](example-agent/rfc-trigger-mechanism_2.md) | rfc: Trigger/Mux 机制设计 | 0 | ✅ PQ mux + 三级订阅 + timer 延后 |
| example-agent | [#3](example-agent/feat-unified-mcp-tools_3.md) | feat: 统一走 MCP Client | 0/2 | ✅ 内嵌 MCP Server (组合模式), read_mailbox 延后 |
| example-agent | [#4](example-agent/feat-dual-agent-shell_4.md) | feat: 双 Agent + shell-server | 4 | — |
| python-sdk-mcp | [#1](python-sdk-mcp/feat-subscribe-levels_1.md) | feat: 细粒度订阅 + read_mailbox | 1 | ✅ sidecar + level 参数 |
| python-sdk-mcp | [#2](python-sdk-mcp/docs-mcp-server-positioning_2.md) | docs: MCP Server = capability | 1 | — |
| example-inference | [#1](example-inference/feat-mcp-sampling_1.md) | feat: MCP Sampling 支持 | 1 | ✅ Agent 端 sampling handler |
| mcp-interfaces | [#1](mcp-interfaces/feat-full-stack-schemas_1.md) | feat: 全栈消息 Schema | 1 | — |
| mcp-gateway | [#1](mcp-gateway/feat-mock-external-server_1.md) | feat: Mock 外部 Server 测试包 | 3 | ✅ stdio+HTTP, 新仓库 |
| example-memory | [#1](example-memory/feat-rollback-support_1.md) | feat: 无感持久化+断点重续 | 3 | ✅ 去掉rollback (Q5) |
| example-frontend | [#1](example-frontend/feat-multi-agent-monitor_1.md) | feat: 多 Agent 监控 | 3 | — |
| example-bringup | [#1](example-bringup/feat-full-stack-launch_1.md) | feat: 全栈启动配置 | 4 | — |
| container-orchestrator | [#1](container-orchestrator/feat-bringup-integration_1.md) | feat: Bringup 集成 | 3 | — |
| test-bringup | [#2](test-bringup/feat-full-stack-system-test_2.md) | feat: 全栈 System 测试 | 4 | — |

### Phase 0 决议摘要 (✅ 全部完成)

1. **Trigger 机制** → PriorityQueue mux, 三级订阅 (UNSUBSCRIBED/SILENT/TRIGGER), sidecar timer 延后
2. **统一 MCP** → AgentNode 内嵌 MCP Server (agent-local tools), 统一 MCP Client, read_mailbox 延后
3. **细粒度订阅** → sidecar 方案, subscribe_topic(level), set_subscription_level(topic, level)
4. **MCP Sampling** → Inference 不变 (Bus Service), Agent MCP Client 实现 sampling handler
5. **Mock External Server** → stdio+HTTP 都测, 新建 `mock-external-server` 独立仓库

### 哲学对齐分析补充决议 (ALIGNMENT_ANALYSIS.md)

6. **Q1**: `/alarm` schema 移除 — timer 不在 v1 范围
7. **Q2**: AgentNode + MCP Server 采用**组合模式** (has-a, not is-a)
8. **Q3**: InferenceMux priority 可配置, v1 用简单默认值
9. **Q4**: read_mailbox 延后合理 — 邮箱 drain 是进程内操作
10. **Q5**: Memory 去掉 rollback, 只做无感持久化 + 断点重续

### AgentNode 架构 & SDK 重组决议 (2026-03-15, ALIGNMENT_ANALYSIS Q6-Q11)

11. **Q6**: AgentNode 组件 (`MessageQueue`/`InferenceMux`/`ContextFactory`) → **新建 python-sdk-agent**
12. **Q7**: TagentacleMCPServer = **内核接口** (独立进程), 非 AgentNode 插件; AgentNode 的 MCP Server = 桌面插件
13. **Q8**: `MCPServerNode` 基类**废除** → **MCPServerComponent** 可组合组件 (FastMCP+uvicorn, 不继承 Node)
14. **Q9**: LifecycleNode lifecycle event **保留** (与 ROS 2 一致)
15. **Q10**: TACL 拆为独立包 **python-sdk-tacl**, 换用 **PyJWT** (精选而非发明)
16. **Q11**: `PermissionMCPServerNode` → **TACLAuthority**

## 依赖顺序 & 具体 Feat 列表

```
Phase 0: 讨论 & 决议 ✅ DONE
```

### Phase 1: 基础设施 (可并行)

| 仓库 | Issue | 具体 feat |
|------|-------|-----------|
| mcp-interfaces | [#1](mcp-interfaces/feat-full-stack-schemas_1.md) | `ChatInput.json`, `ChatOutput.json`, `MemorySnapshot.json`, `AgentMessage.json` 新增; tagentacle.toml 映射注册 |
| python-sdk-mcp | [#1](python-sdk-mcp/feat-subscribe-levels_1.md) | `subscribe_topic(topic, level)` level 参数扩展; `set_subscription_level(topic, level)` 新 MCP tool; sidecar 模式同进程信任 |
| python-sdk-mcp | [#2](python-sdk-mcp/docs-mcp-server-positioning_2.md) | **MCPServerNode 废除 → MCPServerComponent 组件化** (Q8); 组合模式文档 (Q2); MCP Gateway README 传输层定位 |
| python-sdk-mcp | NEW | **TACL 代码拆出** → 新建 python-sdk-tacl; 换用 PyJWT; PermissionMCPServerNode → TACLAuthority (Q10, Q11) |
| python-sdk-agent | NEW | **新建包**: MessageQueue, InferenceMux, ContextFactory 可复用组件 (Q6) |
| example-inference | [#1](example-inference/feat-mcp-sampling_1.md) | Agent 端: MCP Client 注册 sampling handler → 内部 `call_service("/inference/chat", msgs)` → 返回 sampling result; Inference 本身不改 |

### Phase 2: Agent 重构

| 仓库 | Issue | 具体 feat |
|------|-------|-----------|
| example-agent | [#1](example-agent/refactor-mailbox-agent-node_1.md) | 组件来自 python-sdk-agent (Q6); `AgentNode._run_inference_cycle()` 编排 (~150 行); 总 <500 行 |
| example-agent | [#3](example-agent/feat-unified-mcp-tools_3.md) | AgentNode **组合** MCPServerComponent (桌面插件, Q7/Q8); 作为 MCP Client 连接 TagentacleMCPServer (内核接口, Q7); built_in_tools 彻底消除 |

### Phase 3: 支撑节点

| 仓库 | Issue | 具体 feat |
|------|-------|-----------|
| example-memory | [#1](example-memory/feat-rollback-support_1.md) | 错误恢复+重试; Session 元数据; payload 符合 MemorySnapshot.json schema (rollback 已移除 Q5) |
| example-frontend | [#1](example-frontend/feat-multi-agent-monitor_1.md) | 双 agent 聊天历史并排显示; 指定 agent 发消息; 系统节点状态面板; session 状态查看 |
| mcp-gateway | [#1](mcp-gateway/feat-mock-external-server_1.md) | **新建 `mock-external-server` 仓库**; tools: `echo(text)`, `get_time()`, `add(a,b)`; 同时提供 stdio + HTTP 入口 |
| container-orchestrator | [#1](container-orchestrator/feat-bringup-integration_1.md) | tagentacle.toml `type=executable` 验证; system_launch.toml 声明; podman socket bringup 可用性; TACL agent 授权容器服务 |

### Phase 4: 编排 & 测试

| 仓库 | Issue | 具体 feat |
|------|-------|-----------|
| example-bringup | [#1](example-bringup/feat-full-stack-launch_1.md) | `system_launch.toml` 全栈拓扑声明; `system_launch.py` 按依赖序启动; `tagentacle setup dep --all` 拉全量依赖 |
| example-agent | [#4](example-agent/feat-dual-agent-shell_4.md) | agent_node_1 (指令入口) + agent_node_2 (执行者); 通过 topic 通信; 共享 shell-server; 各自独立 memory session |
| test-bringup | [#2](test-bringup/feat-full-stack-system-test_2.md) | `@system` 测试: dual-agent 通信, MCP gateway relay, memory 持久化+恢复, container ops, frontend 接收; CI Layer 4 手动执行 |

## GitHub 项目管理方案

> ✅ 已决议

- **GitHub Projects V2**: https://github.com/orgs/Tagentacle/projects/1
- **Labels**: 每个相关仓库打 `project:full-stack-v1` 标签 (开工时创建)
- **PR workflow**: 每个仓库独立 PR, 通过 Project board 关联
- **本地 issue → GitHub**: 按需推送 — 开始实施某个 issue 时才推送到 GitHub, 同时 `gh project item-add`
- **本地 issues/ 目录是 single source of truth**, GitHub 用于协作和可见性
