# Tagentacle 哲学 × full-stack-v1 对齐分析

> 分析日期: 2026-03-14
> 目的: 确保 full-stack-v1 每个 feature 与 Tagentacle 核心设计哲学一致

---

## Tagentacle 7 条核心设计原则

| # | 原则 | 一句话 |
|---|------|--------|
| P1 | **一切皆包** | Agent/Tool/Interface/Bringup 四种包类型，乐高式组合 |
| P2 | **领域 Shell** | 不替代 Linux，在其上构建域语义层（如 HTTP 之于 TCP） |
| P3 | **操作系统 vs 超级应用** | Daemon 只管总线+生命周期，每个 Pkg 独立进程 |
| P4 | **提供机制，不绑策略** | 邮箱是机制，触发阈值是策略；subscribe 是机制，初始列表是策略 |
| P5 | **端到端原则** | 智能在端点（SDK/Node），不在网络（Daemon） |
| P6 | **精选而非发明** | pub/sub 40 年了，JSON Schema 15 年了，我们选子集和默认值 |
| P7 | **网状拓扑，对等节点** | 没有主角，Agent 只是总线上一个节点 |

---

## 逐 Feature 对齐矩阵

### Phase 1: 基础设施

| Feature | P1 | P2 | P3 | P4 | P5 | P6 | P7 | 问题 |
|---------|----|----|----|----|----|----|----|----|
| mcp-interfaces: Schema | ✅ Interface Pkg | — | — | — | ✅ 端点验证 | ✅ JSON Schema 标准 | — | ⚠️ Q1 |
| python-sdk-mcp: 订阅级别 | — | — | — | ✅ level=机制, 选哪个=策略 | ✅ SDK 层, daemon 不改 | — | — | — |
| python-sdk-mcp: MCP 定位文档 | — | — | ✅ capability非类型 | — | ✅ 端点能力 | — | ✅ 任何节点可选 | ⚠️ Q2 |
| example-inference: Sampling | — | — | ✅ Inference 保持独立节点 | ✅ handler=机制 | ✅ Agent 端处理 | — | ✅ 对等调用 | — |

### Phase 2: Agent 重构

| Feature | P1 | P2 | P3 | P4 | P5 | P6 | P7 | 问题 |
|---------|----|----|----|----|----|----|----|----|
| AgentNode 邮箱架构 | ✅ Agent Pkg | — | ✅ Agent≠主进程 | ✅ MQ+Mux=机制, prompt=策略 | ✅ 智能在 Agent 端 | — | ✅ Agent是对等节点 | ⚠️ Q3, Q4 |
| 统一 MCP Client | ✅ Pkg 边界清晰 | — | ✅ 去 built_in | ⚠️ MCP Server 嵌入方式 | ✅ 端到端 | ✅ MCP 协议标准 | — | ⚠️ Q2 |

### Phase 3: 支撑节点

| Feature | P1 | P2 | P3 | P4 | P5 | P6 | P7 | 问题 |
|---------|----|----|----|----|----|----|----|----|
| Memory 回滚 | ✅ Service Pkg | — | ✅ 独立进程 | — | — | ✅ JSON 文件存储 | ✅ 对等 service | ⚠️ Q5 |
| Frontend 监控 | ✅ Pkg | — | ✅ 独立进程 | — | — | — | ✅ 订阅观察 | ⚠️ Q5 |
| Mock External Server | ✅ 新建独立仓库 | — | ✅ 独立 Pkg | — | ✅ MCP 端点 | ✅ 标准 MCP 协议 | — | — |
| Container Bringup | ✅ Tool Pkg | ✅ 复用 Podman | — | ✅ TACL=机制 | — | — | — | — |

### Phase 4: 编排 & 测试

| Feature | P1 | P2 | P3 | P4 | P5 | P6 | P7 | 问题 |
|---------|----|----|----|----|----|----|----|----|
| Bringup 全栈 | ✅ Bringup Pkg | — | — | ✅ TOML=策略, 启动=机制 | — | — | — | — |
| 双 Agent | ✅ Agent Pkg ×2 | — | — | ✅ prompt 定角色=策略 | — | — | ✅ 对等, topic 通信 | — |
| System 测试 | ✅ 在 test-bringup Pkg | — | — | — | — | — | — | — |

---

## 5 个对齐问题 — 决议记录

### Q1: /alarm Schema — 移除 ✅

**决议**: `/alarm` schema **从 mcp-interfaces #1 移除**。full-stack-v1 不做 timer/alarm, 无需占位 schema。
Timer 相关设计等未来 v2+ 再议。

---

### Q2: AgentNode 嵌入 MCP Server — 组合模式 ✅

**决议**: 采用**组合模式** — `AgentNode(LifecycleNode)` 包含一个 `TagentacleMCPServer` 实例。MCP Server 是可选能力，不是类型继承。

**对齐分析**:
- P4（不绑策略）: 不是所有 agent 都需要 MCP Server 能力。继承强制绑定。
- P1（一切皆包）: MCPServerNode 是 SDK 层概念, AgentNode 是 Agent Pkg 层。层级不同。
- P3（OS not Super-App）: 组合让 AgentNode 保持轻量, 按需加载 MCP。
- docs: "MCP Server = interface capability（不是 Node 类型）"

代码形态: `self.mcp_server = TagentacleMCPServer(...)` (has-a, not is-a)

---

### Q3: InferenceMux 优先级 — 可配置 ✅

**决议**: priority mapping 为**可配置** (subscribe 时指定或用默认值)。v1 先用简单默认值: TRIGGER → 正常入队, SILENT → 不触发推理。不阻塞实现。

**对齐分析**: P4 要求 Mux 只提供"排队+执行"机制, 不硬编码优先级规则。

---

### Q4: read_mailbox 延后 — 合理 ✅

**决议**: v1 使用内部 `self.mailbox.drain()` 读取邮箱，**完全合理**。无需修改。

**对齐分析**:
- 邮箱是 Agent 自己的内存数据结构, 读自己的内存 ≠ 总线操作
- P5（端到端）: 端点内部如何组织数据是端点的自由
- 未来 read_mailbox MCP tool 的价值是**允许外部访问**（如 frontend 调试），而非 Agent 自调用

---

### Q5: Memory — 去掉 Rollback, 只做无感持久化 + 断点重续 ✅

**决议**: Memory **不做 rollback**。只做:
1. **无感持久化**: Agent publish `/memory/latest` → Memory 自动写磁盘 (已实现)
2. **断点重续**: Agent 启动时调 `/memory/load` → 恢复上次 session (已实现)

**变更影响**:
- example-memory #1 "回滚支持" → 重新定义或关闭
- example-frontend #1 不再需要 "rollback 操作入口"
- `/memory/rollback`, `/memory/versions`, `/memory/diff` 三个 service 均不实现

**对齐分析**:
- P4（不绑策略）: 持久化和恢复是机制, 何时恢复/恢复到哪里是策略 — Agent 自己决定
- P6（精选）: 不做不需要的功能 — YAGNI
- 当前 memory.py 已满足需求, 无需增加复杂度

---

## 总结

| 分类 | 数量 | 说明 |
|------|------|------|
| **完全对齐** | 9/14 | 无问题 |
| **已决策** | 5/14 | Q1-Q5 全部关闭 |

**整体评价**: full-stack-v1 与 Tagentacle 哲学**高度对齐**。5 个发现的问题均已决策关闭, 没有根本性哲学冲突。

### 决议清单

| # | 决议 | 影响 |
|---|------|------|
| Q1 | `/alarm` schema 从 mcp-interfaces #1 移除 | mcp-interfaces #1 |
| Q2 | AgentNode + MCP Server 采用组合模式 (has-a) | python-sdk-mcp #2, example-agent #3 |
| Q3 | InferenceMux priority 可配置, v1 用简单默认值 | example-agent #1 |
| Q4 | read_mailbox 延后合理, 邮箱 drain 是进程内操作 | example-agent #1, #3 |
| Q5 | Memory 去掉 rollback, 只做无感持久化 + 断点重续 | example-memory #1, example-frontend #1 |

---

## 第二轮讨论: AgentNode 架构 & SDK 重组 (2026-03-15)

### 背景

Q2 确认了"组合模式"，但进一步讨论后发现需要更深层的架构调整。

### Q6: AgentNode 组件 → 新建 python-sdk-agent ✅

**决议**: `MessageQueue` / `InferenceMux` / `ContextFactory` 从 `example-agent` 拆出，新建 **python-sdk-agent** 包。

**原因**: 这些是可复用的 Agent 基础构件，不应只活在 example 仓库。其他 Agent 实现也需要邮箱+Mux+Context工厂。

### Q7: TagentacleMCPServer 层级纠正 ✅

**决议**: TagentacleMCPServer 是**内核接口** (kernel interface)，独立运行为单独进程/节点，不是 AgentNode 的插件。

| 层级 (OS 隐喻) | 角色 | Tagentacle 中 |
|---------------|------|---------------|
| **内核接口** (syscall) | 总线操作暴露为 MCP tools | TagentacleMCPServer — 独立进程 |
| **桌面插件** (GNOME Ext) | 应用级 MCP tools | AgentNode 自己的 MCPServerComponent |

- TagentacleMCPServer 不嵌入 AgentNode
- AgentNode 作为 MCP Client 连接 TagentacleMCPServer
- AgentNode 可选地运行自己的 MCPServerComponent 暴露 agent-specific tools

### Q8: MCPServerNode 废除 → MCPServerComponent 组件化 ✅

**决议**: 废除 `MCPServerNode(LifecycleNode)` 继承基类，MCP Server 能力变为可组合的 `MCPServerComponent`。

**变更前**:
```
Node → LifecycleNode → MCPServerNode → TagentacleMCPServer
                                      → PermissionMCPServerNode
```

**变更后**:
```
MCPServerComponent (独立组件, 不继承 Node)
  - FastMCP 实例
  - uvicorn 启停管理
  - /mcp/directory 发布方法 (调用者决定何时发布)

TagentacleMCPServer(LifecycleNode)
  - has-a MCPServerComponent
  - 注册 bus tools

TACLAuthority(LifecycleNode)  [原 PermissionMCPServerNode]
  - has-a MCPServerComponent
  - 注册 auth tools
  - 内嵌 SQLite

WeatherServer(LifecycleNode)  [example-mcp-server]
  - has-a MCPServerComponent
  - 注册自定义 tools
```

**关键**: MCPServerNode.on_activate 里的自动 uvicorn 启动和 /mcp/directory 发布是**策略**，不应焊在基类。组件化后由使用者自行编排。

### Q9: LifecycleNode lifecycle event 保留 ✅

**决议**: 保留 `_publish_lifecycle_event`，与 ROS 2 行为一致。节点状态变化发到 `/tagentacle/node_events` 是 OS 级机制，不是策略。

### Q10: TACL 独立成包 python-sdk-tacl ✅

**决议**: 将 TACL 从 python-sdk-mcp 拆出为独立包 **python-sdk-tacl**。

包含:
- **TACL 原语**: JWT sign/verify, CallerIdentity (换用 **PyJWT** — P6 精选)
- **TACL 中间件**: TACLAuthMiddleware (Starlette)
- **TACL 客户端**: AuthMCPClient → TACLClient
- **TACL 节点**: PermissionMCPServerNode → **TACLAuthority**

**PyJWT 替换**: 移除手写 HS256 JWT (~60行)，引入 PyJWT 依赖。支持 RS256/ES256 以备未来需要。

### Q11: PermissionMCPServerNode → TACLAuthority ✅

**决议**: 重命名为 `TACLAuthority`。职责: JWT 发行 + Agent 注册表管理 (SQLite) + 鉴权 MCP tools。

v1 范围: 仅 MCP tool 级授权。未来可扩展 Bus 级鉴权等。

---

### 决议清单 (Q6-Q11)

| # | 决议 | 影响 |
|---|------|------|
| Q6 | AgentNode 组件 → 新建 python-sdk-agent | example-agent, 新建仓库 |
| Q7 | TagentacleMCPServer = 内核接口, 独立进程 | example-agent #3 架构变更 |
| Q8 | MCPServerNode 废除 → MCPServerComponent 组件 | python-sdk-mcp 重构 |
| Q9 | LifecycleNode lifecycle event 保留 (如 ROS 2) | 不变 |
| Q10 | TACL 拆为 python-sdk-tacl, 换用 PyJWT | python-sdk-mcp 瘦身, 新建仓库 |
| Q11 | PermissionMCPServerNode → TACLAuthority | python-sdk-tacl |
