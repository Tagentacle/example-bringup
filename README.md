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
| `launch/system_launch.py` | Config-driven launcher with topological ordering |
| `config/secrets.toml` | API keys and credentials (git-ignored) |
| `config/secrets.toml.example` | Template showing expected secret keys |
| `tagentacle.toml` | Package manifest (type: bringup) + workspace repo deps |

## Secrets Management

```bash
cp config/secrets.toml.example config/secrets.toml
# Edit config/secrets.toml with your API keys
```

Secrets are automatically injected as environment variables to all launched nodes.

## Project Documentation

This bringup repo sits at the top of the dependency graph, making it the natural home for project-level documents:

| Document | Description |
|----------|-------------|
| [docs/PROJECT_FULL_STACK_V1.md](docs/PROJECT_FULL_STACK_V1.md) | Full-stack-v1 master plan: topology, phases, decisions |
| [docs/ALIGNMENT_ANALYSIS.md](docs/ALIGNMENT_ANALYSIS.md) | Philosophy ↔ feature alignment analysis (Q1-Q11) |
| [docs/KANBAN.md](docs/KANBAN.md) | Progress tracking board |

→ [GitHub Project board](https://github.com/orgs/Tagentacle/projects/1)
