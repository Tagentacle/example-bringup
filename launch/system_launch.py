"""
Tagentacle Bringup Launcher: Config-driven topology orchestration.

Reads system_launch.toml and:
1. Starts the Tagentacle Daemon
2. Launches nodes in dependency order with parameter injection
3. Manages graceful shutdown

Usage:
    python launch/system_launch.py                   # Uses launch/system_launch.toml
    python launch/system_launch.py my_config.toml    # Custom config
"""

import asyncio
import os
import signal
import sys

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for Python 3.10
    except ImportError:
        tomllib = None

# Paths setup
LAUNCH_DIR = os.path.dirname(os.path.abspath(__file__))
BRINGUP_DIR = os.path.dirname(LAUNCH_DIR)
# Workspace root: the directory containing the bringup pkg (and sibling pkgs)
WORKSPACE_DIR = os.path.dirname(BRINGUP_DIR)


def load_config(config_path: str) -> dict:
    """Load launch configuration from TOML file."""
    if tomllib is None:
        print("Error: tomllib not available. Install tomli for Python 3.10.")
        sys.exit(1)

    with open(config_path, "rb") as f:
        return tomllib.load(f)


async def run_process(cmd: str, cwd: str, name: str, env: dict = None):
    """Run a subprocess with output logging."""
    print(f"[{name}] Starting: {cmd}")
    merged_env = {**os.environ, **(env or {})}

    # Use package venv if available
    venv_python = os.path.join(cwd, ".venv", "bin", "python")
    if os.path.isfile(venv_python) and cmd.startswith("python "):
        cmd = venv_python + cmd[6:]  # Replace 'python' with venv python path

    process = await asyncio.create_subprocess_shell(
        cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=merged_env,
        start_new_session=True,  # each child gets its own process group
    )

    async def log_output():
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            print(f"[{name}] {line.decode().strip()}")

    asyncio.create_task(log_output())
    return process


def resolve_package_dir(package_name: str) -> str:
    """Resolve package name to its directory in the workspace.

    Searches for the package by its tagentacle.toml name in sibling
    directories of the bringup package. Supports both kebab-case repo
    dirs and snake_case package names.
    """
    # Direct match (sibling directory with same name, or kebab-case)
    for candidate_name in [package_name, package_name.replace("_", "-")]:
        pkg_dir = os.path.join(WORKSPACE_DIR, candidate_name)
        if os.path.isdir(pkg_dir):
            return pkg_dir

    # Scan all sibling directories for matching tagentacle.toml name
    if tomllib is not None:
        for entry in os.listdir(WORKSPACE_DIR):
            entry_path = os.path.join(WORKSPACE_DIR, entry)
            toml_path = os.path.join(entry_path, "tagentacle.toml")
            if os.path.isfile(toml_path):
                try:
                    with open(toml_path, "rb") as f:
                        pkg_toml = tomllib.load(f)
                    if pkg_toml.get("package", {}).get("name") == package_name:
                        return entry_path
                except Exception:
                    pass

    raise FileNotFoundError(
        f"Package '{package_name}' not found in workspace {WORKSPACE_DIR}. "
        f"Run `tagentacle setup dep --all {WORKSPACE_DIR}` to clone dependencies."
    )


async def main():
    # Load config
    config_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(LAUNCH_DIR, "system_launch.toml")
    )
    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    print(f"--- Tagentacle Bringup: loaded {config_path} ---")

    # Extract parameters for env injection
    params = config.get("parameters", {})
    inject_env = {k: str(v) for k, v in params.items() if isinstance(v, str)}

    # Load secrets file and inject as env vars
    secrets_cfg = config.get("secrets", {})
    secrets_file = secrets_cfg.get("secrets_file", "")
    if secrets_file:
        secrets_path = os.path.join(BRINGUP_DIR, secrets_file)
        if os.path.isfile(secrets_path):
            inject_env["TAGENTACLE_SECRETS_FILE"] = secrets_path
            try:
                with open(secrets_path, "rb") as sf:
                    secret_data = tomllib.load(sf)
                for k, v in secret_data.items():
                    if isinstance(v, str):
                        inject_env[k] = v
                print(
                    f"[BRINGUP] Loaded {len(secret_data)} secret(s) from {secrets_path}"
                )
            except Exception as e:
                print(f"[BRINGUP] Warning: failed to load secrets: {e}")
        else:
            print(f"[BRINGUP] Secrets file not found: {secrets_path} (skipped)")

    processes = []
    shutdown_event = asyncio.Event()

    def _signal_handler():
        if not shutdown_event.is_set():
            print("\n--- Bringup: received shutdown signal ---")
            shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    # 1. Start Daemon (skip if already running)
    daemon_addr = config.get("daemon", {}).get("addr", "127.0.0.1:19999")
    daemon_host, daemon_port = daemon_addr.rsplit(":", 1)
    daemon_running = False
    try:
        import socket

        with socket.create_connection((daemon_host, int(daemon_port)), timeout=1.0):
            daemon_running = True
            print(f"[BRINGUP] Daemon already running at {daemon_addr}")
    except OSError:
        pass

    if not daemon_running:
        daemon_proc = await run_process(
            f"tagentacle daemon --addr {daemon_addr}", WORKSPACE_DIR, "DAEMON"
        )
        processes.append(("DAEMON", daemon_proc))
        await asyncio.sleep(3)
    else:
        await asyncio.sleep(1)

    # 2. Launch nodes in order (respecting depends_on)
    nodes = config.get("nodes", [])
    launched = set()

    for node_cfg in nodes:
        name = node_cfg["name"]
        package = node_cfg["package"]
        command = node_cfg["command"]
        depends = node_cfg.get("depends_on", [])
        delay = node_cfg.get("startup_delay", 1)

        # Wait for dependencies
        for dep in depends:
            if dep not in launched:
                print(f"[{name}] Waiting for dependency '{dep}'...")
                await asyncio.sleep(delay)

        # Per-node env: check for NAME_KEY pattern in parameters
        node_env = dict(inject_env)
        prefix = name.upper() + "_"
        for k, v in params.items():
            if k.startswith(prefix):
                real_key = k[len(prefix) :]
                node_env[real_key] = str(v)

        pkg_dir = resolve_package_dir(package)
        proc = await run_process(command, pkg_dir, name, env=node_env)
        processes.append((name, proc))
        launched.add(name)

        if delay > 0:
            await asyncio.sleep(delay)

    # 3. Wait for last node OR shutdown signal
    if processes:
        last_name, last_proc = processes[-1]
        print(
            f"[BRINGUP] Waiting for '{last_name}' to complete (Ctrl-C to stop all)..."
        )
        wait_task = asyncio.create_task(last_proc.wait())
        signal_task = asyncio.create_task(shutdown_event.wait())
        done, _ = await asyncio.wait(
            [wait_task, signal_task], return_when=asyncio.FIRST_COMPLETED
        )
        for t in (wait_task, signal_task):
            if not t.done():
                t.cancel()

    # 4. Graceful shutdown
    await _shutdown_all(processes)


async def _shutdown_all(processes, timeout: float = 10.0):
    """SIGTERM all process groups, wait, then SIGKILL stragglers."""
    if not processes:
        return
    print("--- Bringup: Shutting down all nodes ---")

    # Phase 1: SIGTERM every process group (reverse order)
    for name, proc in reversed(processes):
        if proc.returncode is not None:
            continue
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGTERM)
            print(f"[{name}] SIGTERM sent (pgid={pgid})")
        except (ProcessLookupError, OSError):
            pass

    # Phase 2: wait for graceful exit
    async def _wait(name, proc):
        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
            print(f"[{name}] exited (code={proc.returncode})")
        except asyncio.TimeoutError:
            # Phase 3: SIGKILL
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
                print(f"[{name}] SIGKILL sent")
            except (ProcessLookupError, OSError):
                pass

    await asyncio.gather(*[_wait(n, p) for n, p in processes])
    print("--- Bringup complete ---")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBringup interrupted — cleaning up...")
        # Processes are in their own session groups, so any survivors
        # from asyncio.run() teardown are already handled by _shutdown_all
        # which runs in the normal exit path (step 4).
        # This catch is only for the case where Ctrl-C arrives before
        # any processes are launched.
