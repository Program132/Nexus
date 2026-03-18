import os
import docker
import sys
from Logger import Logger


class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException:
            Logger.error("Failed to connect to Docker. Ensure Docker Desktop is running.")
            sys.exit(1)
        self.image_name = "nexus-env:latest"

    def is_image_built(self) -> bool:
        try:
            self.client.images.get(self.image_name)
            return True
        except docker.errors.ImageNotFound:
            return False

    def build_image(self):
        dockerfile_path = os.path.join(os.getcwd(), "docker")
        Logger.info("🏗️  Building Nexus Docker image (this may take a few minutes on the first run)...")
        try:
            response = self.client.api.build(
                path=dockerfile_path,
                tag=self.image_name,
                decode=True
            )
            for chunk in response:
                if 'stream' in chunk:
                    sys.stdout.write(chunk['stream'])
                    sys.stdout.flush()
                elif 'error' in chunk:
                    Logger.error(f"Docker build error: {chunk['error']}")
                    return False
            Logger.success(f"Image {self.image_name} successfully built!")
            return True
        except Exception as e:
            Logger.error(f"Failed to build Docker image: {str(e)}")
            return False

    def start_workspace(self, workspace_name: str, host_network: bool = False):
        container_name = f"nexus_workspace_{workspace_name}"
        Logger.info(f"Connecting to workspace {workspace_name}...")
        if host_network:
            Logger.info("Host network mode enabled — container shares the host's IP and interfaces.")
        try:
            container = self.client.containers.get(container_name)
            if container.status != 'running':
                Logger.info("Workspace was stopped, restarting...")
                container.start()
            Logger.success(f"Workspace {workspace_name} attached to Docker container.")
            self._setup_visuals(container, workspace_name)
            return container
        except docker.errors.NotFound:
            Logger.info("Creating a new container for this workspace...")
            try:
                local_dir = os.path.join(os.getcwd(), "workspaces", workspace_name)
                os.makedirs(local_dir, exist_ok=True)
                run_kwargs = dict(
                    name=container_name,
                    detach=True,
                    tty=True,
                    cap_add=["NET_RAW", "NET_ADMIN", "NET_BROADCAST", "SYS_PTRACE"],
                    security_opt=["seccomp=unconfined"],
                    network_mode="host" if host_network else "bridge",
                    devices=["/dev/net/tun:/dev/net/tun"],
                    volumes={
                        local_dir: {
                            'bind': '/workspace',
                            'mode': 'rw'
                        }
                    }
                )
                if not host_network:
                    run_kwargs["ports"] = {"1080/tcp": 1080}
                container = self.client.containers.run(self.image_name, **run_kwargs)
                Logger.success(f"Container {container_name} successfully created.")
                self._setup_visuals(container, workspace_name)
                return container
            except Exception as e:
                Logger.error(f"Error creating Docker container: {str(e)}")
                return None

    def _setup_visuals(self, container, workspace_name: str):
        container.exec_run("touch /root/.hushlogin")

        ps1 = (
            r"\[\e[38;2;189;189;189m\]["
            r"\[\e[38;2;71;224;4m\]" + workspace_name + r"\[\e[38;2;189;189;189m\]] "
            r"\[\e[38;2;145;4;141m\]["
            r"\[\e[38;2;84;101;255m\]\w"
            r"\[\e[38;2;145;4;141m\]] "
            r"\[\e[38;2;255;140;0m\](session) "
            r"\[\e[38;2;220;220;220m\]> "
            r"\[\e[0m\]"
        )
        bashrc_cmd = (
            f"sed -i '/# nexus_prompt/d' /root/.bashrc && "
            f"echo 'export PS1=\"{ps1}\" # nexus_prompt' >> /root/.bashrc"
        )
        container.exec_run(["/bin/bash", "-c", bashrc_cmd])

        functions = (
            "upload() {\n"
            "  local src=\"$1\" dest_name=\"${2:-$(basename \"$1\")}\";\n"
            "  if [ -z \"$src\" ]; then\n"
            "    echo \"[nexus] Usage: upload <path_in_container> [dest_name]\"; return 1;\n"
            "  fi;\n"
            "  cp -r \"$src\" \"/workspace/$dest_name\" && "
            f"echo \"[nexus] Copied to /workspace/$dest_name  (Windows: workspaces\\\\{workspace_name}\\\\$dest_name)\";\n"
            "}\n"
            "download() {\n"
            "  local f=\"$1\";\n"
            "  if [ -z \"$f\" ]; then\n"
            "    echo \"[nexus] Usage: download <filename_in_workspace>\"; return 1;\n"
            "  fi;\n"
            "  if [ -e \"/workspace/$f\" ]; then\n"
            f"    echo \"[nexus] Available on Windows at: workspaces\\\\{workspace_name}\\\\$f\";\n"
            "  else\n"
            "    echo \"[nexus] /workspace/$f does not exist.\"; return 1;\n"
            "  fi;\n"
            "}\n"
        )
        write_cmd = f"cat > /root/.nexus_functions << 'NEXUS_EOF'\n{functions}NEXUS_EOF"
        container.exec_run(["/bin/bash", "-c", write_cmd])
        source_cmd = (
            "grep -q 'nexus_functions' /root/.bashrc || "
            "echo 'source /root/.nexus_functions # nexus_functions' >> /root/.bashrc"
        )
        container.exec_run(["/bin/bash", "-c", source_cmd])

    def open_session(self, workspace_name: str, session_id: str, env: dict = None, external: bool = False, session_type: str = "interactive"):
        import sys
        container_name = f"nexus_workspace_{workspace_name}"
        env_flags = " ".join(f"-e {k}={v}" for k, v in (env or {}).items())
        
        if session_type == "interactive":
            try:
                container = self.client.containers.get(container_name)
                container.exec_run(["bash", "-c", "which tmux || apt-get install -y tmux >/dev/null 2>&1"])
                container.exec_run(["bash", "-c", 'echo "set -g status off" > /root/.tmux.conf'])
                container.exec_run(["bash", "-c", f"tmux new-session -d -s {session_id} bash -l 2>/dev/null"])
                attach_cmd = f"tmux attach -t {session_id}"
                exit_hint = "Ctrl+B then D to detach (keeps history), 'exit' to KILL shell"
            except Exception:
                attach_cmd = "bash -l"
                exit_hint = "'exit' or Ctrl+D to return"
        else:
            attach_cmd = "bash -l"
            exit_hint = "'exit' or Ctrl+D to return"
            
        full_cmd = f"docker exec -it -e TERM=xterm-256color {env_flags} {container_name} {attach_cmd}"
        
        if external and sys.platform == "win32":
            Logger.info(f"Opening Session '{session_id}' in a new Windows Terminal pane...")
            import shutil
            if shutil.which("wt"):
                os.system(f'wt -p "Command Prompt" --title "Nexus - Session {session_id}" cmd /c "{full_cmd}"')
            else:
                os.system(f'start "Nexus - Session {session_id}" cmd /c "{full_cmd}"')
        else:
            if external:
                Logger.warning("External terminal is only supported on Windows currently.")
            Logger.log_color(f"┌─ Session '{session_id}' ─ prompt is orange inside ─ {exit_hint}", "#ff8c00")
            os.system(full_cmd)
            Logger.log_color("└─ Back in Nexus", "#ff8c00")

    def run_background_session(self, workspace_name: str, session_id: str, cmd: str) -> bool:
        container_name = f"nexus_workspace_{workspace_name}"
        log_file = f"/tmp/nexus_logs_{session_id}.log"
        try:
            container = self.client.containers.get(container_name)
            container.exec_run(
                ["bash", "-c", f"({cmd}) > {log_file} 2>&1"],
                detach=True
            )
            return True
        except Exception as e:
            Logger.error(f"Failed to start background session: {e}")
            return False

    def get_session_logs(self, workspace_name: str, session_id: str) -> str | None:
        container_name = f"nexus_workspace_{workspace_name}"
        log_file = f"/tmp/nexus_logs_{session_id}.log"
        try:
            container = self.client.containers.get(container_name)
            exit_code, output = container.exec_run(["cat", log_file])
            if exit_code != 0:
                return None
            return output.decode("utf-8", errors="replace")
        except Exception as e:
            Logger.error(f"Failed to read logs: {e}")
            return None

    def stop_workspace(self, workspace_name: str):
        container_name = f"nexus_workspace_{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            if container.status == 'running':
                Logger.info(f"Stopping workspace {workspace_name}...")
                container.stop(timeout=5)
        except Exception:
            pass

    def start_ovpn(self, workspace_name: str, ovpn_file: str):
        container_name = f"nexus_workspace_{workspace_name}"
        log_file = "/tmp/nexus_ovpn.log"
        ovpn_path = f"/workspace/{ovpn_file}"
        try:
            container = self.client.containers.get(container_name)
            container.exec_run(["bash", "-c", "pkill -f openvpn 2>/dev/null; sleep 0.5"])
            container.exec_run(
                ["bash", "-c", f"(openvpn {ovpn_path}) > {log_file} 2>&1"],
                detach=True
            )
        except Exception:
            pass

    def stop_ovpn(self, workspace_name: str):
        container_name = f"nexus_workspace_{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            container.exec_run(["bash", "-c", "pkill -f openvpn 2>/dev/null"])
        except Exception:
            pass

    def get_ovpn_status(self, workspace_name: str) -> dict:
        container_name = f"nexus_workspace_{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            exit_code, _ = container.exec_run(["bash", "-c", "pgrep -f openvpn >/dev/null 2>&1"])
            if exit_code != 0:
                return {"running": False}
            _, raw = container.exec_run(["bash", "-c", "ip -4 addr show tun0 2>/dev/null | awk '/inet /{print $2}' | head -1"])
            tun_ip = raw.decode().strip()
            return {"running": True, "tun_ip": tun_ip}
        except Exception:
            return {"running": False}

    def start_http_server(self, workspace_name: str, port: int):
        container_name = f"nexus_workspace_{workspace_name}"
        log_file = "/tmp/nexus_http_server.log"
        try:
            container = self.client.containers.get(container_name)
            container.exec_run(["bash", "-c", "pkill -f 'python3 -m http.server' 2>/dev/null; sleep 0.5"])
            container.exec_run(
                ["bash", "-c", f"(cd /workspace && python3 -m http.server {port}) > {log_file} 2>&1"],
                detach=True
            )
        except Exception:
            pass

    def stop_http_server(self, workspace_name: str):
        container_name = f"nexus_workspace_{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            container.exec_run(["bash", "-c", "pkill -f 'python3 -m http.server' 2>/dev/null"])
        except Exception:
            pass

    def get_http_server_status(self, workspace_name: str) -> dict:
        container_name = f"nexus_workspace_{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            exit_code, _ = container.exec_run(["bash", "-c", "pgrep -f 'python3 -m http.server' >/dev/null 2>&1"])
            return {"running": exit_code == 0}
        except Exception:
            return {"running": False}

    def execute_command(self, workspace_name: str, command: str, workdir: str = "/workspace"):
        Logger.warning("This mode is deprecated. Please use 'nexus session new' to get a real interactive terminal.")
