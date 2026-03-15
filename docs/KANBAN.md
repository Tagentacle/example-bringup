# Tagentacle 项目看板

> 更新时间: 2026-03-15

---

## ✅ Done (已合并到 main)

### 本轮提交 (2026-03-14)

| 提交 | 仓库 | 内容 |
|------|------|------|
| `3d858e3` | python-sdk-core | ci: simplify to lint-only |
| `96a25db` | python-sdk-mcp | ci: simplify to lint-only |
| `250dfa7` | container-orchestrator | ci: simplify to lint-only + ruff format |
| `9ef8a9d` | shell-server | ci: simplify to lint-only |
| `5221a4d` | test-bringup | ci: simplify to lint-only + ruff format |
| `b16e8e7` | tagentacle | feat: lint 子命令 + test 最小依赖声明 (#9, #10) |
| `afe2edd` | python-sdk-core | feat: lifecycle state events + test config (#1) |
| `1803a89` | test-bringup | chore: add test config section |

### 上轮提交 (2026-03-13)

| 提交 | 仓库 | 内容 |
|------|------|------|
| `5eae60f` | python-sdk-core | ci: uv 迁移, Layer 1 lint+build, v0.3.1 |
| `679e1d3` | python-sdk-mcp | ci: uv 迁移, Layer 1 lint+build, v0.4.1 |
| `bcc111c` | container-orchestrator | fix: podman-py 4.x 兼容 + CI + build-system, v0.2.1 |
| `c0add72` | shell-server | fix: ruff format + CI + build-system, v0.2.1 |
| `8522222` | tagentacle | fix: health check messages + cargo fmt |
| `be6df69` | test-bringup | feat: +27 tests, CI Layer 对齐, @e2e→@system, v0.2.0 |

### 之前提交

| 提交 | 仓库 | 内容 |
|------|------|------|
| `361e9fa` | tagentacle | feat: `tagentacle test` 子命令 |
| `0943d1d` | tagentacle | fix: install dir bug |
| `8a70085` | test-bringup | refactor: flat tests/ + smart conftest |
| `c825034` | test-bringup | feat: 13 tests passing |
| `84fc58f` | tagentacle | docs: 文档重组 |

---

## CI 分层架构 (已落地)

> **2026-03-14 精简**: GHA CI 退化为 badge 门面, 去掉 build/integration job (sibling checkout 路径冲突)。
> 所有 Python 仓库统一为 lint-only; tagentacle (Rust) 保留完整 CI。6/6 repos CI ✅。

| Layer | 名称 | GHA | 本地 | 强制 |
|-------|------|-----|------|------|
| 1 | lint | ✅ ruff check + fmt (5 Python repos) | `tagentacle lint` (手动) | ❌ |
| 1 | lint+build+test | ✅ cargo check/clippy/test/fmt (tagentacle) | — | ❌ |
| 2 | pkg test | ❌ 需 daemon | `tagentacle test --pkg` | ❌ |
| 3 | integration | ❌ 已从 GHA 移除 | `tagentacle test --all` | ❌ |
| 4 | system | ❌ 手动 | pytest -m system | ❌ |

---

## 🟡 Todo — Issues (已建档, 待后续迭代)

> ✅ 本轮关闭: #8 CI RFC, #9 lint, #10 test deps, #1 test markers, #1 lifecycle events

### Daemon 特性

| Issue | 仓库 | 优先级 | 描述 |
|-------|------|--------|------|
| [#2](tagentacle/feat-describe-topic-schema_2.md) | tagentacle | 中 | **describe_topic_schema** — Daemon 实现系统服务, MCP tool 端到端 |
| [#4](tagentacle/feat-schema-hash_4.md) | tagentacle | 中 | **schema hash registry** — ADVERTISE/SUBSCRIBE 可选 hash 匹配, 依赖 #2 |

### 架构演进

| Issue | 仓库 | 优先级 | 描述 |
|-------|------|--------|------|
| [#7](tagentacle/feat-transport-layer_7.md) | tagentacle | 低 | **transport layer (rmw)** — TCP/Unix/WS 抽象, 单机够用暂不急 |

---

## 🔴 Project: full-stack-v1 — 全功能测试 (14 issues → GitHub ✅)

> 详见 [PROJECT_FULL_STACK_V1.md](PROJECT_FULL_STACK_V1.md) | [ALIGNMENT_ANALYSIS.md](ALIGNMENT_ANALYSIS.md)
> GitHub Board: https://github.com/orgs/Tagentacle/projects/1 (14 items)
> **2026-03-15**: 全部 14 issue 已同步到 GitHub repos + Project Board

### Phase 0: 讨论 & 决议 (✅ 全部完成)

| Issue | 仓库 | 描述 | 决议摘要 |
|-------|------|------|----------|
| [#2](example-agent/rfc-trigger-mechanism_2.md) | example-agent | rfc: Trigger/Mux 机制 | ✅ 优先级 PQ; 三级订阅; 闹钟 sidecar 延后 |
| [#3](example-agent/feat-unified-mcp-tools_3.md) | example-agent | feat: 统一走 MCP Client | ✅ 内核接口/桌面插件层级; MCPServerComponent 组件化 |
| [#1](python-sdk-mcp/feat-subscribe-levels_1.md) | python-sdk-mcp | feat: 细粒度订阅 + read_mailbox | ✅ sidecar; read_mailbox 延后单独 pkg |
| [#1](example-inference/feat-mcp-sampling_1.md) | example-inference | feat: MCP Sampling 支持 | ✅ Inference 不变; Agent 实现 sampling handler |
| [#1](mcp-gateway/feat-mock-external-server_1.md) | mcp-gateway | feat: Mock 外部 Server | ✅ stdio+HTTP 都测; 新建独立仓库 |

### Phase 1: 基础设施

| Issue | 仓库 | 描述 | 状态 |
|-------|------|------|------|
| [#1](mcp-interfaces/feat-full-stack-schemas_1.md) | mcp-interfaces | 全栈消息 Schema | open |
| [#2](python-sdk-mcp/docs-mcp-server-positioning_2.md) | python-sdk-mcp | MCPServerNode → MCPServerComponent 组件化 | open |
| [#1](python-sdk-mcp/feat-subscribe-levels_1.md) | python-sdk-mcp | 细粒度订阅 (三级) | open |
| NEW | python-sdk-mcp | TACL 拆出 → python-sdk-tacl + PyJWT | open |
| NEW | python-sdk-agent | 新建包: MessageQueue/InferenceMux/ContextFactory | open |
| [#1](example-inference/feat-mcp-sampling_1.md) | example-inference | Agent sampling handler | open |

### Phase 2: Agent 重构

| Issue | 仓库 | 描述 | 状态 |
|-------|------|------|------|
| [#1](example-agent/refactor-mailbox-agent-node_1.md) | example-agent | AgentNode 邮箱架构 (组件 from python-sdk-agent) | open |
| [#3](example-agent/feat-unified-mcp-tools_3.md) | example-agent | MCP Client → TagentacleMCPServer(内核) + MCPServerComponent(桌面) | open |

### Phase 3: 支撑节点

| Issue | 仓库 | 描述 | 状态 |
|-------|------|------|------|
| [#1](example-memory/feat-rollback-support_1.md) | example-memory | 无感持久化 + 断点重续 (rollback 已移除) | open |
| [#1](example-frontend/feat-multi-agent-monitor_1.md) | example-frontend | 多 Agent 监控 | open |
| [#1](mcp-gateway/feat-mock-external-server_1.md) | mcp-gateway | Mock 外部 Server (新仓库) | open |
| [#1](container-orchestrator/feat-bringup-integration_1.md) | container-orchestrator | Bringup 集成 | open |

### Phase 4: 编排 & 测试

| Issue | 仓库 | 描述 | 状态 |
|-------|------|------|------|
| [#1](example-bringup/feat-full-stack-launch_1.md) | example-bringup | 全栈启动配置 | open |
| [#4](example-agent/feat-dual-agent-shell_4.md) | example-agent | 双 Agent + shell-server | open |
| [#2](test-bringup/feat-full-stack-system-test_2.md) | test-bringup | 全栈 System 测试 | open |

---

## 环境备忘

| 项 | 值 |
|----|----|
| OS | Ubuntu 22.04 LTS (N100) |
| Podman | 4.6.2 (rootless, user socket enabled) |
| podman-py | 4.9.0 (兼容 Podman 4.x) |
| uv | 已安装, CI 统一工具链 |
| tagentacle | v0.4.0 |
| python-sdk-core | v0.3.1 |
| python-sdk-mcp | v0.4.1 |
| container-orchestrator | v0.2.1 |
| shell-server | v0.2.1 |
| test-bringup | v0.2.0 |
