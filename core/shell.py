import sys
import os
from Logger import Logger
from .workspace import Workspace
from .commands import CommandManager
from .docker_manager import DockerManager

class Shell:
    def __init__(self, workspace: Workspace, docker_mgr: DockerManager):
        self.workspace = workspace
        self.docker_mgr = docker_mgr
        self.command_manager = CommandManager(docker_mgr)

    def _cleanup(self):
        import sys
        pid = self.workspace.ovpn.get("host_pid")
        connect_id = self.workspace.ovpn.get("ovpn_connect_id")
        
        if connect_id and sys.platform == "win32":
            windows_ovpn_connect = r"C:\Program Files\OpenVPN Connect\OpenVPNConnect.exe"
            os.system(f'"{windows_ovpn_connect}" --disconnect >nul 2>&1')
            os.system(f'"{windows_ovpn_connect}" --remove-profile={connect_id} >nul 2>&1')
        elif pid:
            if sys.platform == "win32":
                os.system(f"taskkill /F /PID {pid} >nul 2>&1")
            else:
                os.system("sudo pkill -f 'openvpn --config' >/dev/null 2>&1")
            
        self.docker_mgr.stop_ovpn(self.workspace.name)
        self.docker_mgr.stop_http_server(self.workspace.name)
        self.workspace.save()
        self.docker_mgr.stop_workspace(self.workspace.name)

    def start(self):
        import atexit
        atexit.register(self._cleanup)
        
        self.workspace.load()

        Logger.banner()

        if self.workspace.is_new and not self.workspace.sessions and not self.workspace.notes:
            Logger.info(f"Creating new workspace: {self.workspace.name}...")
        else:
            Logger.info(f"Opening existing workspace: {self.workspace.name}...")

        if self.workspace.save_enabled:
            Logger.info("Auto-save is ENABLED for this workspace.")
        else:
            Logger.info("Auto-save is DISABLED for this workspace.")

        print()

        try:
            while True:
                path_display = "/workspace"
                if self.workspace.active_session_id:
                    path_display = f"/{self.workspace.active_session_id}"

                prompt = Logger.set_texts_color(
                    ["[", f"{self.workspace.name}", "]", " [", f"{path_display}", "]", " (nexus) ", "> "],
                    ["#bdbdbd", "#47e004", "#bdbdbd", "#91048d", "#5465ff", "#91048d", "#0ba5d4", "#a6a6a6"],
                    ""
                )
                command_line = input(prompt).strip()
                if command_line:
                    self.workspace.history.append(command_line)
                    self.command_manager.execute(command_line, self.workspace)
                    self.workspace.save()
        except (KeyboardInterrupt, EOFError):
            print()
            self._cleanup()
            sys.exit(0)
