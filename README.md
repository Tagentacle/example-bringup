# example_bringup

A **Bringup Package** that orchestrates the entire Tagentacle example system.

Users only need to clone this single repo — all dependency repos are auto-cloned
by `tagentacle setup dep --all`.

## Quick Start

```bash
# 1. Create a workspace and clone this bringup
mkdir -p my_workspace/src && cd my_workspace/src
git clone https://github.com/Tagentacle/example-bringup.git

# 2. Install everything (auto-clones example-agent, example-mcp-server)
cd ..
tagentacle setup dep --all .

# 3. Launch the system
tagentacle launch src/example-bringup/launch/system_launch.toml
```

## What it does

1. Declares dependency repos in `tagentacle.toml` → `[workspace.repos]`
2. `tagentacle setup dep --all` reads these and auto-clones missing repos
3. `system_launch.toml` defines the topology: which nodes, startup order, parameters
4. The launcher starts the Daemon, then nodes in dependency order
5. Secrets are injected from `config/secrets.toml` (git-ignored)

## Files

| File | Description |
|------|-------------|
| `launch/system_launch.toml` | Topology config: nodes, dependencies, parameters |
| `config/secrets.toml` | API keys and credentials (git-ignored) |
| `config/secrets.toml.example` | Template showing expected secret keys |
| `tagentacle.toml` | Package manifest (type: bringup) + workspace repo deps |

## Secrets Management

```bash
cp config/secrets.toml.example config/secrets.toml
# Edit config/secrets.toml with your API keys
```

Secrets are automatically injected as environment variables to all launched nodes.

## System Architecture

```
                     ┌── example-frontend (Gradio 监控) ──┐
                     │                                     │
 ┌─── [broker] ──────┼── agent_node_1 ──┐                  │
 │    19999          │── agent_node_2 ──┤                  │
 │                   │                  ▼                  │
 │    Topics:        │          BusMCPNode                  │
 │    /chat/*        │          (InboxMCP buffer            │
 │    /memory/*      │           via MCP)                   │
 │    /mcp/directory │                  │                  │
 │                   │                  ▼                  │
 │    Services:      │     ┌── shell-mcp (MCP) ─────┐     │
 │    /inference/chat│     │── example-mcp-server ──│     │
 │    /memory/load   │     │── mock-external (MCP) ─│     │
 │    /memory/list   │     └────────────────────────┘     │
 │    /nodes/*       │                                     │
 │    /containers/*  │  container-orchestrator              │
 │                   │                                     │
 │                   ├── example-inference                  │
 │                   ├── example-memory                     │
 │                   ├── mcp-gateway (relay mock-external)  │
 │                   └── bus-connector-mcp (外部 MCP 桥)    │
 └────────────────────────────────────────────────────────┘
```

## Org-level Documentation

| Document | Location |
|----------|----------|
| Full-stack-v1 R&D plan | [issues/PROJECT_FULL_STACK_V1.md](https://github.com/Tagentacle/Tagentacle.github.io) |
| Philosophy alignment analysis | [issues/ALIGNMENT_ANALYSIS.md](https://github.com/Tagentacle/Tagentacle.github.io) |
| Project kanban | [GitHub Project board](https://github.com/orgs/Tagentacle/projects/1) |
