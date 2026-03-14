import argparse
import sys
from Logger import Logger
from core.workspace import Workspace
from core.shell import Shell

class NexusApp:
    def __init__(self):
        self.parser = self._setup_argparse()

    def _setup_argparse(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Nexus - Ethical Hacking Framework")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-n", "--name", type=str, help="Create or open a workspace with the given name")
        group.add_argument("-o", "--open", type=str, help="Open a workspace you previously saved")
        parser.add_argument("-s", "--save", action="store_true", help="Save the progress in your workspace")
        parser.add_argument("-H", "--host-network", action="store_true",
                            help="Share the host network stack (same IP). Best on Linux.")
        return parser

    def run(self):
        args = self.parser.parse_args()
        workspace_name = args.name if args.name else args.open
        save_path = args.save
        is_new = bool(args.name)
        host_network = args.host_network

        if not workspace_name.strip():
            Logger.error("Workspace name cannot be empty.")
            sys.exit(1)

        workspace = Workspace(name=workspace_name, is_new=is_new, save_enabled=save_path)

        from core.docker_manager import DockerManager
        docker_mgr = DockerManager()

        if not docker_mgr.is_image_built():
            success = docker_mgr.build_image()
            if not success:
                sys.exit(1)

        container = docker_mgr.start_workspace(workspace.name, host_network=host_network)
        if not container:
            sys.exit(1)

        shell = Shell(workspace, docker_mgr)
        shell.start()

if __name__ == "__main__":
    app = NexusApp()
    app.run()